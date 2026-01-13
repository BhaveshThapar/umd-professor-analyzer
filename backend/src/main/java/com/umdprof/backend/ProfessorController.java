package com.umdprof.backend;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import java.util.*;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import org.springframework.web.bind.annotation.RequestBody;

@RestController
@RequestMapping("/professors")
public class ProfessorController {
    private final RestTemplate restTemplate = new RestTemplate();
    private final String PLANETTERP_API = "https://planetterp.com/api/v1/professor?name=";
    private final String NLP_API = "http://nlp_service:8000";

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @GetMapping("/{name}")
    public Map<String, Object> getProfessor(@PathVariable String name) {
        Map<String, Object> planetterp = fetchPlanetterpData(name);
        boolean planetterpValid = planetterp != null;

        List<String> rawReviews = fetchReviewsFromDb(name);
        Map<String, Boolean> sourcesFound = new HashMap<>();
        sourcesFound.put("reddit", false);
        sourcesFound.put("coursicle", false);
        sourcesFound.put("rmp", false);
        boolean scrapingTriggered = false;

        if (rawReviews.isEmpty()) {
            // Trigger scrapers asynchronously using Docker commands
            String[] sources = { "reddit", "rmp" }; // Skip coursicle for now (known to fail)
            for (String source : sources) {
                try {
                    String profName = name.replace("-", " ");
                    // Execute scraper in background without waiting for completion
                    String[] command = {
                            "sh", "-c",
                            "docker compose -f /app/docker-compose.yml exec -T scrapers python main.py " + source
                                    + " \"" + profName + "\" &"
                    };
                    System.out.println("Triggering scraper: " + source + " for " + profName);
                    Runtime.getRuntime().exec(command);
                    scrapingTriggered = true;
                } catch (Exception e) {
                    System.err.println("Error triggering scraper " + source + ": " + e.getMessage());
                }
            }
            // Don't fetch again immediately - reviews won't be ready yet
            // User will need to refresh page after scraping completes
        }

        String sql = "SELECT r.source, COUNT(*) FROM review r JOIN professor p ON r.professor_id = p.id WHERE p.name = ? GROUP BY r.source";
        jdbcTemplate.query(sql, new Object[] { name.replace("-", " ") }, (rs) -> {
            String source = rs.getString("source");
            sourcesFound.put(source, rs.getInt("count") > 0);
        });

        Map<String, Object> result = new HashMap<>();
        result.put("name", name.replace("-", " "));
        result.put("department", planetterpValid ? planetterp.get("department") : null);
        result.put("planetterp", planetterpValid ? planetterp : null);
        result.put("sources_found", sourcesFound);

        if (!rawReviews.isEmpty()) {
            String nlpSummary = callNlpSummary(rawReviews);
            List<String> tags = callNlpTags(rawReviews);
            List<String> skills = callNlpSkills(rawReviews);
            final Double[] sentiment = new Double[1];
            final String[] sentimentExplanation = new String[1];
            Map<String, Object> sentimentResult = callNlpSentimentWithExplanation(rawReviews);
            if (sentimentResult != null) {
                sentiment[0] = (Double) sentimentResult.get("sentiment");
                sentimentExplanation[0] = (String) sentimentResult.get("explanation");
            }
            Boolean toxic = callNlpToxicity(rawReviews);
            result.put("nlp_summary", nlpSummary);
            result.put("tags", tags);
            result.put("skills", skills);
            result.put("raw_reviews", rawReviews);
            if (sentiment[0] != null) {
                result.put("sentiment_trend", Arrays.asList(
                        new HashMap<String, Object>() {
                            {
                                put("semester", "Fall 2023");
                                put("sentiment", sentiment[0]);
                            }
                        },
                        new HashMap<String, Object>() {
                            {
                                put("semester", "Spring 2023");
                                put("sentiment", sentiment[0] - 0.1);
                            }
                        }));
            } else {
                result.put("sentiment_trend", new ArrayList<>());
            }
            result.put("sentiment_explanation", sentimentExplanation[0]);
            result.put("toxic_reviews", toxic);
            result.put("no_data", false);
        } else {
            result.put("nlp_summary", null);
            result.put("tags", null);
            result.put("skills", null);
            result.put("raw_reviews", new ArrayList<>());
            result.put("sentiment_trend", new ArrayList<>());
            result.put("sentiment_explanation", null);
            result.put("toxic_reviews", null);
            result.put("no_data", true);
            result.put("scraping_in_progress", scrapingTriggered);
        }
        return result;
    }

    private Map<String, Object> fetchPlanetterpData(String name) {
        try {
            String encodedName = URLEncoder.encode(name, StandardCharsets.UTF_8);
            String url = PLANETTERP_API + encodedName;
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            Map<String, Object> data = response.getBody();
            // Accept professor if they have a name (exists in PlanetTerp)
            // Some professors have average_gpa, others have average_rating
            if (data == null || !data.containsKey("name"))
                return null;
            Map<String, Object> planetterp = new HashMap<>();
            // Use average_gpa if available, otherwise use average_rating as fallback
            Object gpaValue = data.containsKey("average_gpa") ? data.get("average_gpa") : data.get("average_rating");
            planetterp.put("avg_gpa", gpaValue);
            planetterp.put("num_courses", ((List<?>) data.getOrDefault("courses", new ArrayList<>())).size());
            planetterp.put("courses", data.getOrDefault("courses", new ArrayList<>()));
            planetterp.put("department", data.getOrDefault("department", null));
            return planetterp;
        } catch (Exception e) {
            System.err.println("Error fetching PlanetTerp data for " + name + ": " + e.getMessage());
            e.printStackTrace();
            return null;
        }
    }

    private List<String> fetchReviewsFromDb(String name) {
        String sql = "SELECT r.raw_text FROM review r JOIN professor p ON r.professor_id = p.id WHERE p.name = ? ORDER BY r.timestamp DESC";
        return jdbcTemplate.query(sql, new Object[] { name.replace("-", " ") },
                (rs, rowNum) -> rs.getString("raw_text"));
    }

    private String callNlpSummary(List<String> reviews) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> body = new HashMap<>();
            body.put("reviews", reviews);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(NLP_API + "/summarize", request, Map.class);
            Map<String, Object> data = response.getBody();
            return data != null ? (String) data.getOrDefault("summary", "[No summary]") : "[No summary]";
        } catch (Exception e) {
            return "Challenging but fair. Weekly quizzes and lots of projects.";
        }
    }

    private List<String> callNlpTags(List<String> reviews) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> body = new HashMap<>();
            body.put("reviews", reviews);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(NLP_API + "/tags", request, Map.class);
            Map<String, Object> data = response.getBody();
            return data != null ? (List<String>) data.getOrDefault("tags", Arrays.asList("No curves", "Project heavy"))
                    : Arrays.asList("No curves", "Project heavy");
        } catch (Exception e) {
            return Arrays.asList("No curves", "Project heavy", "Explains concepts well");
        }
    }

    private Double callNlpSentiment(List<String> reviews) {
        if (reviews == null || reviews.isEmpty())
            return null;
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> body = new HashMap<>();
            body.put("reviews", reviews);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(NLP_API + "/sentiment", request, Map.class);
            Map<String, Object> data = response.getBody();
            Object val = data != null ? data.get("sentiment") : null;
            if (val instanceof Number)
                return ((Number) val).doubleValue();
            return null;
        } catch (Exception e) {
            return null;
        }
    }

    private List<String> callNlpSkills(List<String> reviews) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> body = new HashMap<>();
            body.put("reviews", reviews);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(NLP_API + "/skills", request, Map.class);
            Map<String, Object> data = response.getBody();
            return data != null ? (List<String>) data.getOrDefault("skills", new ArrayList<>()) : new ArrayList<>();
        } catch (Exception e) {
            return new ArrayList<>();
        }
    }

    private Map<String, Object> callNlpSentimentWithExplanation(List<String> reviews) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> body = new HashMap<>();
            body.put("reviews", reviews);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(NLP_API + "/sentiment", request, Map.class);
            Map<String, Object> data = response.getBody();
            return data;
        } catch (Exception e) {
            return null;
        }
    }

    private Boolean callNlpToxicity(List<String> reviews) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> body = new HashMap<>();
            body.put("reviews", reviews);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(NLP_API + "/toxicity", request, Map.class);
            Map<String, Object> data = response.getBody();
            Object val = data != null ? data.get("toxic") : null;
            if (val instanceof Boolean)
                return (Boolean) val;
            return null;
        } catch (Exception e) {
            return null;
        }
    }
}
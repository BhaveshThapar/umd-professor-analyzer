package com.umdprof.backend;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import java.util.*;

@RestController
@RequestMapping("/professors")
public class ProfessorController {
    private final RestTemplate restTemplate = new RestTemplate();
    private final String PLANETTERP_API = "https://api.planetterp.com/v1/professor?name=";
    private final String NLP_API = "http://nlp_service:8000";

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @GetMapping("/{name}")
    public Map<String, Object> getProfessor(@PathVariable String name) {
        Map<String, Object> planetterp = fetchPlanetterpData(name);

        List<String> rawReviews = fetchReviewsFromDb(name);
        if (rawReviews.isEmpty()) {
            rawReviews = Arrays.asList("No reviews found.");
        }

        String nlpSummary = callNlpSummary(rawReviews);
        List<String> tags = callNlpTags(rawReviews);
        double sentiment = callNlpSentiment(rawReviews);

        Map<String, Object> result = new HashMap<>();
        result.put("name", name.replace("-", " "));
        result.put("department", planetterp.getOrDefault("department", "CMSC"));
        result.put("planetterp", planetterp);
        result.put("nlp_summary", nlpSummary);
        result.put("tags", tags);
        result.put("raw_reviews", rawReviews);
        result.put("sentiment_trend", Arrays.asList(
            new HashMap<String, Object>() {{
                put("semester", "Fall 2023");
                put("sentiment", sentiment);
            }},
            new HashMap<String, Object>() {{
                put("semester", "Spring 2023");
                put("sentiment", sentiment - 0.1);
            }}
        ));
        return result;
    }

    private Map<String, Object> fetchPlanetterpData(String name) {
        try {
            String url = PLANETTERP_API + name.replace(" ", "%20");
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            Map<String, Object> data = response.getBody();
            if (data == null) return getStubPlanetterp();
            Map<String, Object> planetterp = new HashMap<>();
            planetterp.put("avg_gpa", data.getOrDefault("average_gpa", 2.85));
            planetterp.put("num_courses", ((List<?>)data.getOrDefault("courses", new ArrayList<>())).size());
            planetterp.put("courses", data.getOrDefault("courses", Arrays.asList("CMSC131", "CMSC132")));
            planetterp.put("department", data.getOrDefault("department", "CMSC"));
            return planetterp;
        } catch (Exception e) {
            return getStubPlanetterp();
        }
    }

    private Map<String, Object> getStubPlanetterp() {
        Map<String, Object> planetterp = new HashMap<>();
        planetterp.put("avg_gpa", 2.85);
        planetterp.put("num_courses", 5);
        planetterp.put("courses", Arrays.asList("CMSC131", "CMSC132", "CMSC216", "CMSC330", "CMSC351"));
        planetterp.put("department", "CMSC");
        return planetterp;
    }

    private List<String> fetchReviewsFromDb(String name) {
        String sql = "SELECT r.raw_text FROM review r JOIN professor p ON r.professor_id = p.id WHERE p.name = ? ORDER BY r.timestamp DESC";
        return jdbcTemplate.query(sql, new Object[]{name.replace("-", " ")}, (rs, rowNum) -> rs.getString("raw_text"));
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
            return data != null ? (List<String>) data.getOrDefault("tags", Arrays.asList("No curves", "Project heavy")) : Arrays.asList("No curves", "Project heavy");
        } catch (Exception e) {
            return Arrays.asList("No curves", "Project heavy", "Explains concepts well");
        }
    }

    private double callNlpSentiment(List<String> reviews) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> body = new HashMap<>();
            body.put("reviews", reviews);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(NLP_API + "/sentiment", request, Map.class);
            Map<String, Object> data = response.getBody();
            Object val = data != null ? data.get("sentiment") : null;
            if (val instanceof Number) return ((Number) val).doubleValue();
            return 0.7;
        } catch (Exception e) {
            return 0.7;
        }
    }
} 
FROM maven:3.9.6-eclipse-temurin-21 AS build
WORKDIR /app
COPY . .
RUN mvn clean package -DskipTests

FROM eclipse-temurin:21-jre
WORKDIR /app

# Install Docker CLI to enable triggering scrapers
RUN apt-get update && \
  apt-get install -y curl && \
  curl -fsSL https://get.docker.com -o get-docker.sh && \
  sh get-docker.sh && \
  rm get-docker.sh && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"] 
FROM tomcat:9.0-jdk8-temurin-jammy

COPY web/target/OpenClinica-web-*.war /usr/local/tomcat/webapps/OpenClinica.war
COPY docker/demo/datainfo.properties /usr/local/tomcat/openclinica.config/datainfo.properties

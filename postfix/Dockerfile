FROM ubuntu:20.04

LABEL maintainer="Your Name <your.email@example.com>"

# Install Postfix and SASL2 for authentication
RUN apt-get update && \
    apt-get install -y postfix postfix-sasl procmail mailutils rsyslog && \
    rm -rf /var/lib/apt/lists/*

# Copy Postfix configuration
COPY main.cf /etc/postfix/main.cf

# Copy SASL password file (if using external relay with authentication)
# This file will be created and populated by docker-compose environment variables
COPY sasl_passwd /etc/postfix/sasl_passwd
RUN chmod 600 /etc/postfix/sasl_passwd
RUN postmap /etc/postfix/sasl_passwd

# Expose SMTP port
EXPOSE 25

# Start rsyslog and Postfix
CMD service rsyslog start && postfix start && tail -f /var/log/mail.log
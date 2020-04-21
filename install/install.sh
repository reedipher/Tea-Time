#!/bin/bash

# Prerequisites
printf "\n\n\tInstalling Prerequisites\n\n\n"
sleep 1
sudo apt-get update
sudo apt install -y unzip xvfb libxi6 libgconf-2-4


# Install chrome
printf "\n\n\tInstalling Chrome\n\n\n"
sleep 1
sudo curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add
sudo cp google-chrome.list /etc/apt/sources.list.d/.
sudo apt-get -y update
sudo apt-get -y install google-chrome-stable

# Install chrome driver
printf "\n\n\tInstalling Chrome WebDriver\n\n\n"
sleep 1
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/chromedriver
sudo chown root:root /usr/local/bin/chromedriver
sudo chmod +x /usr/local/bin/chromedriver
sleep 1


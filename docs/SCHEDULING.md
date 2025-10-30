# Job Application Automation Project - Setup Guide

This document provides setup guides for running the job application automation project continuously on macOS, Windows, and Linux. Follow the instructions based on your operating system to ensure your automation runs 24/7.

---

## macOS Setup

### 1. Schedule Automation with Launch Agents

To set up your job automation to run in the background on macOS:

#### Step 1: Create a Launch Agent

1. Open Terminal.
2. Create a new configuration file in `~/Library/LaunchAgents/`. Use the following command to open a new file:
   ```bash
   nano ~/Library/LaunchAgents/com.user.jobautomation.plist
   ```

3. Paste the following configuration into the file:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.user.jobautomation</string>
       <key>ProgramArguments</key>
       <array>
           <string>/path/to/your/seek-automation</string>
       </array>
       <key>RunAtLoad</key>
       <true/>
       <key>StartInterval</key>
       <integer>3600</integer> <!-- Adjust to your desired interval in seconds -->
   </dict>
   </plist>
   ```

4. Save and close the file (Ctrl + X, then Y, then Enter).

#### Step 2: Load the Launch Agent

Run the following command to load your new Launch Agent:
```bash
launchctl load ~/Library/LaunchAgents/com.user.jobautomation.plist
```

### 2. Set the `dateRange`

- To set the range for job searches, open your `run_config` file and modify the `dateRange` parameter:
  ```json
  "dateRange": 2
  ```

---

## Windows Setup

### 1. Schedule Automation with Task Scheduler

For setting up your job automation to run on Windows:

#### Step 1: Open Task Scheduler

1. Press `Windows + R`, type `taskschd.msc`, and hit Enter.
2. In the Task Scheduler, click on **Create Basic Task** from the right pane.

#### Step 2: Configure the Task

1. Name your task (e.g., "Job Application Automation") and click **Next**.
2. Choose the **Trigger** (e.g., Daily) and click **Next**.
3. Set the start time and recurrence based on your preference and click **Next**.
4. Select **Start a program** and click **Next**.
5. Browse for your script and click **Next**, then **Finish**.

### 2. Set the `dateRange`

- In your `run_config` file, update the `dateRange` parameter:
  ```json
  "dateRange": 2
  ```

---

## Linux Setup

### 1. Schedule Automation with Cron

For running your job automation on Linux:

#### Step 1: Edit Crontab File

1. Open Terminal.
2. Use the following command to edit your crontab:
   ```bash
   crontab -e
   ```

#### Step 2: Add a Cron Job

1. Add the following line to schedule your script (this example runs the script every day at midnight):
   ```
   0 0 * * * /path/to/your/seek-automation
   ```

2. Save and exit the editor (typically Ctrl + X, then Y, then Enter).

### 2. Set the `dateRange`

- Change the `dateRange` setting in your `run_config` file:
  ```json
  "dateRange": 2
  ```

---

## Conclusion

By following the steps outlined in this guide for your respective operating system, you can successfully set up the job application automation project to run continuously. Ensure to adjust the `dateRange` according to your preferences to optimize job searches. Happy automating!
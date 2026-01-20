# MoMo - Business Requirements Document (Draft)

**Version:** 1.0  
**Date:** January 20, 2026  
**Project Name:** MoMo  
**Document Status:** Draft for Review

---

## 1. Executive Summary

MoMo is a lightweight Windows utility designed to prevent system idle timeout and maintain "active" presence status in Microsoft Teams. The application monitors user activity and programmatically moves the mouse when idle time exceeds a configurable threshold, ensuring the screen stays awake and collaboration tools reflect an available status.

---

## 2. Business Objectives

| ID | Objective |
|----|-----------|
| BO-1 | Prevent Windows screen timeout during periods of reading, thinking, or passive work |
| BO-2 | Maintain "Available" status in Microsoft Teams without manual intervention |
| BO-3 | Provide a non-intrusive, resource-efficient background utility |

---

## 3. Stakeholders

| Role | Description |
|------|-------------|
| Primary User | Windows 11+ user who needs to prevent idle detection while remaining at their computer |

---

## 4. Functional Requirements

### 4.1 Idle Detection

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | System SHALL monitor both mouse and keyboard activity to determine user idle state | Must |
| FR-1.2 | Idle time threshold SHALL default to 300 seconds (5 minutes) | Must |
| FR-1.3 | Idle time threshold SHALL be configurable in seconds with no restricted range | Must |
| FR-1.4 | Idle timer SHALL reset when any mouse movement or keyboard input is detected | Must |

### 4.2 Mouse Movement

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | System SHALL move the mouse programmatically when idle threshold is exceeded | Must |
| FR-2.2 | Mouse movement SHALL be as imperceptible as possible while still preventing system idle | Must |
| FR-2.3 | System SHALL support multi-monitor configurations | Must |

### 4.3 Schedule Configuration

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | System SHALL support configurable active schedule per day of week | Must |
| FR-3.2 | Each day of week SHALL have independent enable/disable setting | Must |
| FR-3.3 | Each day of week SHALL have configurable start time and stop time | Must |
| FR-3.4 | Schedule times SHALL use the user's system time zone | Must |
| FR-3.5 | Default schedule SHALL be Monday-Friday, 8:00 AM to 5:00 PM | Must |
| FR-3.6 | Default schedule SHALL have Saturday and Sunday disabled | Must |
| FR-3.7 | Mouse movement SHALL only trigger when current time falls within configured active schedule | Must |
| FR-3.8 | System SHALL evaluate schedule in real-time (no restart required for schedule changes) | Should |

### 4.4 User Interface

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | Application SHALL display as a system tray icon only (no main window) | Must |
| FR-4.2 | System tray icon SHALL be a mouse icon with transparent background in normal/monitoring state | Must |
| FR-4.3 | System tray icon background SHALL change to green when actively triggering mouse movement | Must |
| FR-4.4 | Right-click on tray icon SHALL display context menu with configuration options | Must |
| FR-4.5 | Context menu SHALL include option to manually start/stop monitoring | Must |
| FR-4.6 | Context menu SHALL include option to configure idle threshold | Must |
| FR-4.7 | Context menu SHALL include option to configure active schedule | Must |
| FR-4.8 | Context menu SHALL include option to enable/disable auto-start with Windows user login | Must |
| FR-4.9 | Context menu SHALL include option to exit application | Must |

### 4.5 Configuration & Persistence

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | All user settings SHALL persist across application sessions | Must |
| FR-5.2 | Settings SHALL include: idle threshold, auto-start preference, monitoring enabled state, and weekly schedule | Must |
| FR-5.3 | Weekly schedule settings SHALL include for each day: enabled flag, start time, stop time | Must |
| FR-5.4 | Application SHALL load saved settings on startup | Must |

### 4.6 Startup Behavior

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-6.1 | Application SHALL support optional auto-start when user logs into Windows | Must |
| FR-6.2 | Auto-start preference SHALL be configurable by the user | Must |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-1.1 | Application SHALL minimize CPU usage (target: < 1% average) | Must |
| NFR-1.2 | Application SHALL minimize memory footprint (target: < 50 MB) | Should |
| NFR-1.3 | Application SHALL have negligible impact on system performance | Must |

### 5.2 Usability

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-2.1 | Application SHALL be non-intrusive to normal user workflows | Must |
| NFR-2.2 | Application SHALL require no technical knowledge to operate | Should |

### 5.3 Compatibility

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-3.1 | Application SHALL support Windows 11 and later versions | Must |
| NFR-3.2 | Application SHALL function on multi-monitor configurations | Must |

---

## 6. Technical Constraints

| ID | Constraint |
|----|------------|
| TC-1 | Application SHALL be a standalone executable (no installation required) |
| TC-2 | Application SHALL run without administrator privileges |
| TC-3 | Preferred implementation language: Python; acceptable alternative: C# .NET |

---

## 7. User Stories

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| US-1 | As a Windows user, I need the application to detect when I've been idle so that it can take action before my screen times out | Idle detection triggers within configured threshold |
| US-2 | As a Windows user, I need the mouse to move automatically when I'm idle so that my screen doesn't lock and Teams shows me as available | Mouse moves imperceptibly; screen stays awake; Teams status remains "Available" |
| US-3 | As a Windows user, I want to configure the idle threshold so that I can adjust sensitivity to my needs | User can set threshold in seconds via UI |
| US-4 | As a Windows user, I want the app to start automatically when I log in so that I don't have to remember to launch it | Auto-start option works via Windows startup |
| US-5 | As a Windows user, I want to easily pause/resume monitoring so that I can control when the feature is active | Start/Stop toggle accessible from tray menu |
| US-6 | As a Windows user, I want visual feedback when the app moves my mouse so I know it's working | Tray icon background turns green during movement |
| US-7 | As a Windows user, I want to configure which days and times the tool is active so that it only runs during my work hours | Schedule configurable per day with start/stop times; defaults to Mon-Fri 8am-5pm |

---

## 8. Assumptions

1. User has standard Windows 11 user permissions
2. System tray is visible and accessible to the user
3. User's system has standard idle/timeout policies that can be circumvented via mouse input

---

## 9. Out of Scope

| Item | Rationale |
|------|-----------|
| Logging/activity history | Not required per stakeholder |
| Pause during specific applications | Not required per stakeholder |
| Windows 10 or earlier support | Target platform is Windows 11+ |
| Keystroke simulation | Only mouse movement required to prevent idle |

---

## 10. Design Decisions

The following questions were resolved during requirements gathering:

| ID | Question | Decision |
|----|----------|----------|
| DD-1 | **Settings Storage Location** | Settings SHALL be stored in the same directory as the executable to maintain full portability |
| DD-2 | **Movement Frequency** | When idle threshold is reached, mouse SHALL move minimally to prevent Windows/Teams idle detection, then reset the idle timer and repeat the cycle |
| DD-3 | **Error Handling** | Application SHALL display pop-up notifications for errors with user-friendly but complete descriptions and remediation steps where possible |

---

## Document Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Stakeholder | | | |
| Project Lead | | | |

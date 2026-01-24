# How to Test Multiplayer Features Locally

When testing multiplayer features (like Chess or Chat) on a single computer, you must simulate two distinct users.

## The Issue
Web browsers share "session cookies" across all tabs in the same window. 
* If you log in as **Senior** in Tab 1...
* And then log in as **Youth** in Tab 2...
* **Tab 1 is now also logged in as Youth** (in the background).

When you refresh Tab 1, the server sees the Youth cookie and redirects you to the Youth dashboard.

## The Solution
To test properly, you must isolate the sessions:

### Option 1: Incognito / Private Window (Recommended)
1. Open your normal browser window and log in as **Senior**.
2. Open a **New Incognito Window** (Ctrl+Shift+N or Ctrl+Shift+P).
3. In the Incognito window, go to `localhost:5000` and log in as **Youth**.
4. You can now play against yourself without sessions overwriting each other.

### Option 2: Different Browsers
1. Open **Chrome** and log in as Senior.
2. Open **Edge/Firefox** and log in as Youth.

### Option 3: Container Tabs (Firefox only)
If you use Firefox, you can use the "Multi-Account Containers" extension to open tabs with separate cookie jars.

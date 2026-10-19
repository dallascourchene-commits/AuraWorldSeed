module.exports = {
  "testDir": "./11d",
  "testMatch": "**/*.spec.cjs",
  "use": {
    "headless": true,
    "browserName": "chromium"
  },
  "projects": [
    {
      "name": "chromium",
      "use": {
        "browserName": "chromium"
      }
    }
  ],
  "reporter": "line"
};

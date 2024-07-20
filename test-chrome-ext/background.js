// Add Twilio credentials
const TWILIO_ACCOUNT_SID = 'ACfbd0b087e41fd42be2593fafbf8cc56f';
const TWILIO_AUTH_TOKEN = 'b1009be1aed2f34db2b8167050e74b4a';
const TWILIO_PHONE_NUMBER = '+18559601391';

chrome.runtime.onInstalled.addListener(() => {
  chrome.identity.getAuthToken({ interactive: true }, (token) => {
    if (chrome.runtime.lastError) {
      console.error(chrome.runtime.lastError);
      return;
    }
    fetch('http://35.230.77.106/authenticate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
      }
    }).then(response => response.json())
      .then(data => {
        if (data.auth_url) {
          chrome.tabs.create({ url: data.auth_url });
        } else {
          // Store user information in chrome storage
          chrome.storage.local.set({ userInfo: data }, () => {
            console.log('User information stored:', data);
          });
        }
      })
      .catch(error => {
        console.error('Error:', error);
      });
  });

  // Fetch call logs from Twilio and store them
  fetchCallLogs();
});

chrome.browserAction.onClicked.addListener(() => {
  chrome.windows.create({
    url: chrome.runtime.getURL("popup.html"),
    type: "popup",
    width: 800,
    height: 800
  });
});

function fetchCallLogs() {
  fetch(`https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Calls.json`, {
    method: 'GET',
    headers: {
      'Authorization': 'Basic ' + btoa(`${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}`)
    }
  })
  .then(response => response.json())
  .then(data => {
    console.log('Call logs fetched:', data);
    const callLogs = data.calls.map(call => ({
      from: call.from,
      to: call.to,
      url: call.uri.replace('.json', '.html') // Adjust URI for web links
    }));
    chrome.storage.local.set({ callLogs: callLogs }, () => {
      console.log('Call logs stored:', callLogs);
    });
  })
  .catch(error => {
    console.error('Error fetching call logs:', error);
  });
}

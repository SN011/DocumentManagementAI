let userToken = null;

chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed');
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'signIn') {
    authenticate().then(() => {
      execute(sendResponse);
    }).catch(err => {
      console.error('Authentication or API loading error:', err);
      sendResponse({ error: err });
    });
    return true; // Keeps the messaging channel open for sendResponse
  }
});

function authenticate() {
  return new Promise((resolve, reject) => {
    chrome.identity.getAuthToken({ interactive: true }, (token) => {
      if (chrome.runtime.lastError) {
        console.error('Error during getAuthToken:', chrome.runtime.lastError);
        reject(chrome.runtime.lastError.message);
      } else {
        userToken = token;
        resolve();
      }
    });
  });
}

function execute(sendResponse) {
  fetch('https://people.googleapis.com/v1/people/me?personFields=names,emailAddresses,phoneNumbers,photos', {
    headers: {
      'Authorization': 'Bearer ' + userToken
    }
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Failed to fetch user info');
    }
    return response.json();
  })
  .then(data => {
    console.log('Fetched user info:', data); // Log the fetched data

    const name = data.names && data.names.length > 0 ? data.names[0].displayName : 'No name available';
    const email = data.emailAddresses && data.emailAddresses.length > 0 ? data.emailAddresses[0].value : 'No email available';
    const profilePicture = data.photos && data.photos.length > 0 ? data.photos[0].url : 'No picture available';
    const phoneNumber = data.phoneNumbers && data.phoneNumbers.length > 0 ? data.phoneNumbers[0].value : 'No phone number available';

    const userData = {
      name: name,
      email: email,
      picture: profilePicture,
      phoneNumber: phoneNumber
    };

    // Send user data to your Flask server
    fetch('http://127.0.0.1:5000/store-user-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    })
    .then(response => response.text()) // Expect HTML response
    .then(result => {
      console.log('Data sent to Flask server:', result);
      // Display the result in a new window
      const newWindow = window.open();
      newWindow.document.write(result);
      sendResponse({ success: true });
    })
    .catch(error => {
      console.error('Error sending data to Flask server:', error);
      sendResponse({ error });
    });
  })
  .catch(error => {
    console.error('Error fetching user info:', error);
    sendResponse({ error: error.message });
  });
}

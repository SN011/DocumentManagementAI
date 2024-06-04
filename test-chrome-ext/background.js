chrome.runtime.onInstalled.addListener(() => {
  chrome.identity.getAuthToken({ interactive: true }, (token) => {
    if (chrome.runtime.lastError) {
      console.error(chrome.runtime.lastError);
      return;
    }
    fetch('http://localhost:5000/authenticate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
      }
    }).then(response => response.json())
      .then(data => {
        // Store user information in chrome storage
        chrome.storage.local.set({ userInfo: data }, () => {
          console.log('User information stored:', data);
        });
      })
      .catch(error => {
        console.error('Error:', error);
      });
  });
});

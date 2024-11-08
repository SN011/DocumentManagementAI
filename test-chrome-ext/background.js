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
        chrome.storage.local.set({ userInfo: data }, () => {
          console.log('User information stored:', data);
        });
      })
      .catch(error => {
        console.error('Error:', error);
      });
  });
});

chrome.browserAction.onClicked.addListener(() => {
  chrome.windows.create({
    url: chrome.runtime.getURL("popup.html"),
    type: "popup",
    width: 800,
    height: 800
  });
});


//291175256673-vs4cr3oo60mfevlkouc255usb0rokt9q.apps.googleusercontent.com
//291175256673-6m7bkorhc88r3uv3hdum2mfdaoc9jorp.apps.googleusercontent.com
document.getElementById('signInButton').addEventListener('click', () => {
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
          document.getElementById('userName').textContent = data.name;
          document.getElementById('userEmail').textContent = data.email;
          document.getElementById('userPicture').src = data.picture;
          document.getElementById('userInfo').style.display = 'block';
        })
        .catch(error => {
          console.error('Error:', error);
        });
    });
  });

  document.getElementById('savePhoneNumberButton').addEventListener('click', () => {
    const phoneNumber = document.getElementById('phoneNumber').value;
    document.getElementById('displayPhoneNumber').textContent = phoneNumber;
    document.getElementById('phoneNumberDisplay').style.display = 'block';
    document.getElementById('phoneNumberInput').style.display = 'none';
  });
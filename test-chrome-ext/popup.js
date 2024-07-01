let authToken = '';

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');
    checkLoginStatus();

    document.getElementById('signInButton').addEventListener('click', () => {
        console.log('Sign in button clicked');
        chrome.identity.getAuthToken({ interactive: true }, (token) => {
            if (chrome.runtime.lastError) {
                console.error('Error getting auth token:', chrome.runtime.lastError);
                return;
            }
            authToken = token;
            console.log('Auth token obtained:', token);
            fetch('http://localhost:5000/authenticate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                }
            }).then(response => response.json())
                .then(data => {
                    console.log('User data fetched:', data);
                    chrome.storage.local.get(['phoneNumber', 'recEmail'], (result) => {
                        console.log('Existing phone and recemail:', result);
                        data.phone = result.phoneNumber || '';
                        data.recemail = result.recEmail || '';
                        chrome.storage.local.set({ userInfo: data }, () => {
                            console.log('User info stored:', data);
                            displayUserInfo(data);
                            document.getElementById('phoneNumber').value = data.phone;
                            document.getElementById('recEmail').value = data.recemail;
                            document.getElementById('nextButton').style.display = 'block';
                        });
                    });
                })
                .catch(error => {
                    console.error('Error fetching user data:', error);
                });
        });
    });

    document.getElementById('saveCredentialsButton').addEventListener('click', () => {
        const phoneNumber = document.getElementById('phoneNumber').value;
        const recEmail = document.getElementById('recEmail').value;
        const userName = document.getElementById('userName').textContent;
        const userEmail = document.getElementById('userEmail').textContent;

        console.log('Saving credentials:', { phoneNumber, recEmail });

        const credentials = {
            name: userName,
            email: userEmail,
            recemail: recEmail,
            phone: phoneNumber
        };

        fetch('http://localhost:5000/set_credentials', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(credentials)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Credentials saved:', data);
                document.getElementById('phoneNumberDisplay').textContent = phoneNumber;
                document.getElementById('recEmailDisplay').textContent = recEmail;
                document.getElementById('phoneNumberDisplay').style.display = 'block';
                document.getElementById('recEmailDisplay').style.display = 'block';
                document.getElementById('phoneNumberInput').style.display = 'none';
                document.getElementById('recEmailInput').style.display = 'none';
                chrome.storage.local.set({ phoneNumber: phoneNumber, recEmail: recEmail });
            } else {
                console.error('Failed to save credentials:', data.message);
            }
        })
        .catch(error => {
            console.error('Error saving credentials:', error);
        });
    });

    

    document.getElementById('logoutButton').addEventListener('click', () => {
      console.log('Logout button clicked');
      if (authToken) {
          // Revoke the access token
          fetch(`https://accounts.google.com/o/oauth2/revoke?token=${authToken}`, {
              method: 'GET',
              mode: 'cors'
          }).then(response => {
              if (response.ok) {
                  console.log('Access token revoked');
                  clearUserData();
              } else {
                  console.error('Error revoking access token');
                  clearUserData(); // Attempt to clear data even if token revocation fails
              }
          }).catch(error => {
              console.error('Error revoking access token:', error);
              clearUserData(); // Attempt to clear data even if there's an error
          });
      } else {
          console.log('No auth token found');
          clearUserData();
      }
  });
  
  document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');
    checkLoginStatus();

    document.getElementById('nextButton').addEventListener('click', () => {
        console.log('Next button clicked');
        document.getElementById('googleSignIn').style.display = 'none';
        document.getElementById('voiceAssistant').style.display = 'flex';
        document.querySelector('.orb').style.display = 'block';
    });

    document.getElementById('backButton').addEventListener('click', () => {
        console.log('Back button clicked');
        document.getElementById('googleSignIn').style.display = 'flex';
        document.getElementById('voiceAssistant').style.display = 'none';
        document.querySelector('.orb').style.display = 'none';
    });
});


  function clearUserData() {
      chrome.identity.removeCachedAuthToken({ token: authToken }, () => {
          console.log('Auth token removed');
          chrome.storage.local.remove('userInfo', () => {
              console.log('User info removed from storage');
              // Reset the UI
              document.getElementById('userInfo').style.display = 'none';
              document.getElementById('loginPrompt').style.display = 'block';
              document.getElementById('signInButton').style.display = 'block';
              document.getElementById('nextButton').style.display = 'none';
              authToken = '';
              // Ensure orb is hidden
              document.querySelector('.orb').style.display = 'none';
              document.getElementById('googleSignIn').style.display = 'flex';
              document.getElementById('voiceAssistant').style.display = 'none';
          });
      });
  }
  


    document.getElementById('nextButton').addEventListener('click', () => {
        console.log('Next button clicked');
        document.getElementById('googleSignIn').style.display = 'none';
        document.getElementById('voiceAssistant').style.display = 'flex';
        document.querySelector('.orb').style.display = 'block';
    });

    document.getElementById('backButton').addEventListener('click', () => {
        console.log('Back button clicked');
        document.getElementById('googleSignIn').style.display = 'flex';
        document.getElementById('voiceAssistant').style.display = 'none';
        document.querySelector('.orb').style.display = 'none';
    });

    

    let isRecording = false;

    document.addEventListener('keydown', function(event) {
        if (event.key === 'p' || event.key === 'P') {
            if (!isRecording) {
                startRecording();
            }
            else {
                stopRecording();
            }
        }
    });
    
    
    
    function startRecording() {
        console.log('Start recording');
        isRecording = true;
    
        const orb = document.querySelector('.orb');
        orb.classList.add('floating');
    
        fetch('http://localhost:5000/start_recording', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                console.log(data.status);
            });
    }
    
    function stopRecording() {
        console.log('Stop recording');
        isRecording = false;
    
        const orb = document.querySelector('.orb');
        orb.classList.remove('floating');
    
        fetch('http://localhost:5000/stop_recording', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                console.log(data.status);
                // Fetch the audio response after stopping the recording
                fetchAudioResponse();
            });
    }
    
    function fetchAudioResponse() {
        fetch('http://localhost:5000/talk', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                document.getElementById('response').innerText = data.response;
                
                const audio = document.getElementById('audio');
                audio.src = 'http://localhost:5000/get_audio?' + new Date().getTime();
                audio.style.display = 'block';
                audio.play();
            });
    }
    

    function checkLoginStatus() {
        console.log('Checking login status');
        chrome.storage.local.get('userInfo', (result) => {
            if (result.userInfo) {
                console.log('User info found in storage:', result.userInfo);
                displayUserInfo(result.userInfo);
                document.getElementById('phoneNumber').value = result.userInfo.phone || '';
                document.getElementById('recEmail').value = result.userInfo.recemail || '';
                document.getElementById('nextButton').style.display = 'block';
            } else {
                console.log('No user info found in storage');
                document.getElementById('loginPrompt').style.display = 'block';
                document.getElementById('signInButton').style.display = 'block';
                document.getElementById('userInfo').style.display = 'none';
                document.getElementById('nextButton').style.display = 'none';
            }
        });
    }

    function displayUserInfo(data) {
        console.log('Displaying user info:', data);
        document.getElementById('userName').textContent = data.name;
        document.getElementById('userEmail').textContent = data.email;
        document.getElementById('userPicture').src = data.picture;
        document.getElementById('userInfo').style.display = 'block';
        document.getElementById('loginPrompt').style.display = 'none';
        document.getElementById('signInButton').style.display = 'none';
    }
});

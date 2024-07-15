let authToken = '';
let isRecording = false;
let isPlaying = false;
let isHumanToolRequest = false;

let socket = io('http://localhost:5000');

socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('tts_complete', (data) => {
    console.log('TTS synthesis complete:', data.message);
    const audio = document.getElementById('audio');
    audio.src = 'http://localhost:5000/get_audio?' + new Date().getTime();
    audio.style.display = 'block';
    audio.play().catch(error => {
        console.error('Error playing audio:', error);
    });
});

socket.on('new_message', (data) => {
    displayMessage(data.message, data.sender);
});

socket.on('request_human_input', () => {
    console.log('Server is requesting human input');
    document.getElementById('textInput').disabled = false;
    document.getElementById('sendTextButton').disabled = false;
    isHumanToolRequest = true;  // Mark that the next input is for the human tool
});

socket.on('finished_chain', () => {
    console.log('Server is saying the agent exec chain is finished');
    document.getElementById('textInput').disabled = false;
    document.getElementById('sendTextButton').disabled = false;
    isHumanToolRequest = false;  
});

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');
    restoreState();

    document.getElementById('signInButton').addEventListener('click', () => {
        console.log('Sign in button clicked');
        chrome.identity.getAuthToken({ interactive: true }, (token) => {
            if (chrome.runtime.lastError) {
                console.error('Error getting auth token:', chrome.runtime.lastError);
                return;
            }
            authToken = token;
            console.log('Auth token obtained:', token);
            authenticateUser(token);
        });
    });

    document.getElementById('saveCredentialsButton').addEventListener('click', saveCredentials);
    document.getElementById('logoutButton').addEventListener('click', logout);
    document.getElementById('nextButton').addEventListener('click', () => {
        saveState('voiceAssistant');
        showAssistant();
    });
    document.getElementById('backButton').addEventListener('click', () => {
        saveState('credentials');
        showLogin();
    });
    document.getElementById('sendTextButton').addEventListener('click', handleTextInput);
    document.getElementById('textInput').addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            handleTextInput();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'p' || event.key === 'P') {
            const activeElement = document.activeElement;
            if (activeElement && activeElement.id !== 'textInput') {
                if (!isRecording) {
                    startRecording();
                } else {
                    stopRecording();
                }
            }
        }
    });

    checkLoginStatus();
    loadCallLogs();
});

function loadCallLogs() {
    chrome.storage.local.get('callLogs', (result) => {
        if (result.callLogs) {
            console.log('Call logs found in storage:', result.callLogs);
            const callLogsContainer = document.getElementById('callLogsContainer');
            callLogsContainer.innerHTML = '';
            result.callLogs.forEach(log => {
                const link = document.createElement('a');
                link.href = log.url;
                link.textContent = `Call from ${log.from} to ${log.to}`;
                link.target = '_blank';
                callLogsContainer.appendChild(link);
                callLogsContainer.appendChild(document.createElement('br'));
            });
        } else {
            console.log('No call logs found in storage');
        }
    });
}

function authenticateUser(token) {
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
}

function saveCredentials() {
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
            chrome.storage.local.set({ phoneNumber: phoneNumber, recEmail: recEmail }, () => {
                document.getElementById('phoneNumberDisplay').textContent = phoneNumber;
                document.getElementById('recEmailDisplay').textContent = recEmail;
                document.getElementById('phoneNumberDisplay').style.display = 'block';
                document.getElementById('recEmailDisplay').style.display = 'block';
                document.getElementById('phoneNumberInput').style.display = 'none';
                document.getElementById('recEmailInput').style.display = 'none';
            });
        } else {
            console.error('Failed to save credentials:', data.message);
        }
    })
    .catch(error => {
        console.error('Error saving credentials:', error);
    });
}

function logout() {
    console.log('Logout button clicked');
    if (authToken) {
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
}

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
            document.querySelector('.orb').style.display = 'none';
            document.getElementById('googleSignIn').style.display = 'flex';
            document.getElementById('voiceAssistant').style.display = 'none';
        });
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

function handleTextInput() {
    if (isHumanToolRequest) {
        sendHumanInput();
    } else {
        sendTextInput();
    }
}

function sendTextInput() {
    const inputText = document.getElementById('textInput').value;
    if (!inputText.trim()) return;

    displayMessage(inputText, 'user');
    
    fetch('http://localhost:5000/text_input', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: inputText })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Synthesis request sent:', data);
    })
    .catch(error => {
        console.error('Error:', error);
    });

    document.getElementById('textInput').value = '';
}

function sendHumanInput() {
    const inputText = document.getElementById('textInput').value;
    if (!inputText.trim()) return;

    displayMessage(inputText, 'user');

    socket.emit('provide_human_input', { text: inputText });

    document.getElementById('textInput').value = '';
    document.getElementById('textInput').disabled = true;
    document.getElementById('sendTextButton').disabled = true;
    isHumanToolRequest = false;  // Reset the flag
}

function displayMessage(message, sender) {
    const chatWindow = document.getElementById('chatWindow');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;
    messageElement.textContent = message;
    chatWindow.appendChild(messageElement);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

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
            audio.play().catch(error => {
                console.error('Error playing audio:', error);
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function saveState(state) {
    chrome.storage.local.set({ currentState: state }, () => {
        console.log('State saved:', state);
    });
}

function restoreState() {
    chrome.storage.local.get('currentState', (result) => {
        if (result.currentState) {
            console.log('Restoring state:', result.currentState);
            if (result.currentState === 'voiceAssistant') {
                showAssistant();
            } else if (result.currentState === 'credentials') {
                showLogin();
            } else if (result.currentState === 'callLogs') {
                showCallLogs();
            }
        } else {
            console.log('No state found, showing login page');
            showLogin();
        }
    });
}

function showAssistant() {
    document.querySelector('.tab.active').classList.remove('active');
    document.querySelector('.tab-content.active').classList.remove('active');
    document.querySelector('.tab[data-tab="voiceAssistant"]').classList.add('active');
    document.getElementById('voiceAssistant').classList.add('active');
    saveState('voiceAssistant');
}

function showLogin() {
    document.querySelector('.tab.active').classList.remove('active');
    document.querySelector('.tab-content.active').classList.remove('active');
    document.querySelector('.tab[data-tab="googleSignIn"]').classList.add('active');
    document.getElementById('googleSignIn').classList.add('active');
    saveState('credentials');
}

function showCallLogs() {
    document.querySelector('.tab.active').classList.remove('active');
    document.querySelector('.tab-content.active').classList.remove('active');
    document.querySelector('.tab[data-tab="callLogs"]').classList.add('active');
    document.getElementById('callLogs').classList.add('active');
    saveState('callLogs');
}

const TWILIO_ACCOUNT_SID = 'ACfbd0b087e41fd42be2593fafbf8cc56f';
const TWILIO_AUTH_TOKEN = 'b1009be1aed2f34db2b8167050e74b4a';

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');
    restoreState();

    // Automatic sign-in
    chrome.identity.getAuthToken({ interactive: false }, (token) => {
        if (token) {
            authenticateUser(token);
        } else {
            document.getElementById('signInButton').style.display = 'block';
        }
    });

    document.getElementById('signInButton').addEventListener('click', () => {
        console.log('Sign in button clicked');
        chrome.identity.getAuthToken({ interactive: true }, (token) => {
            if (chrome.runtime.lastError) {
                console.error('Error getting auth token:', chrome.runtime.lastError);
                return;
            }
            authenticateUser(token);
        });
    });

    document.getElementById('logout').addEventListener('click', () => {
        chrome.identity.getAuthToken({ interactive: false }, (token) => {
            if (token) {
                chrome.identity.removeCachedAuthToken({ token: token }, () => {
                    console.log('Logged out');
                    chrome.storage.local.remove('userInfo');
                    checkLoginStatus();
                });
            } else {
                console.error('No token found for removal');
            }
        });
    });

    document.getElementById('settings').addEventListener('click', () => {
        document.getElementById('settingsModal').style.display = 'flex';
    });

    document.querySelectorAll('.close').forEach(closeButton => {
        closeButton.addEventListener('click', () => {
            closeButton.closest('.modal').style.display = 'none';
        });
    });

    document.getElementById('toggleTheme').addEventListener('change', (event) => {
        document.body.classList.toggle('light-mode', event.target.checked);
    });

    checkLoginStatus();
    fetchCallLogs();
});

async function fetchCallLogs() {
    try {
        const response = await fetch('http://localhost:5000/fetch-call-logs');
        const data = await response.json();

        if (response.ok) {
            const callLogsContainer = document.getElementById('callLogsContainer');
            if (callLogsContainer) {
                callLogsContainer.innerHTML = ''; // Clear previous logs

                data.forEach((call, index) => {
                    const callElement = document.createElement('div');
                    callElement.className = 'call-log';
                    callElement.dataset.callId = index;

                    const from = call.from || 'Unknown';
                    const startTime = call.start_time || call.date_created || call.date_updated || 'Unknown';
                    const formattedStartTime = formatCallTime(startTime);

                    callElement.innerHTML = `
                        <p style="font-size: 22px"><strong>From:</strong> ${from}</p>
                        <p style="font-size: 22px">${formattedStartTime}</p>
                    `;

                    callLogsContainer.appendChild(callElement);
                });

                // Add event listener for call log clicks
                callLogsContainer.addEventListener('click', function(event) {
                    if (event.target && event.target.closest('.call-log')) {
                        displayCallDetails(event.target.closest('.call-log').dataset.callId);
                    }
                });
            } else {
                console.error('Error: callLogsContainer element not found.');
            }
        } else {
            console.error('Unexpected response format:', data);
            alert(`Error fetching call logs: ${data.error}`);
        }
    } catch (error) {
        console.error('Error fetching call logs:', error);
        alert('Error fetching call logs');
    }
}

function formatCallTime(dateString) {
    const callDate = new Date(dateString);
    if (isNaN(callDate.getTime())) {
        return 'Invalid Date';
    }

    const options = { 
        weekday: 'short', 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
    };
    return callDate.toLocaleString('en-US', options);
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
            chrome.storage.local.get(['phoneNumber', 'recEmail'], (result) => {
                data.phone = result.phoneNumber || '';
                data.recemail = result.recEmail || '';
                chrome.storage.local.set({ userInfo: data }, () => {
                    displayUserInfo(data);
                });
            });
        })
        .catch(error => {
            console.error('Error fetching user data:', error);
        });
}

function displayUserInfo(data) {
    document.getElementById('userPicture').src = data.picture;
    document.getElementById('userPicture').style.display = 'block';
    document.getElementById('signInButton').style.display = 'none';
}

function checkLoginStatus() {
    chrome.storage.local.get('userInfo', (result) => {
        if (result.userInfo) {
            displayUserInfo(result.userInfo);
        } else {
            document.getElementById('signInButton').style.display = 'block';
            document.getElementById('userPicture').style.display = 'none';
        }
    });
}

function saveState(state) {
    chrome.storage.local.set({ currentState: state });
}

function restoreState() {
    chrome.storage.local.get('currentState', (result) => {
        if (result.currentState) {
            showCallLogs();
        } else {
            showCallLogs();
        }
    });
}

function showCallLogs() {
    document.querySelector('.tab.active').classList.remove('active');
    document.querySelector('.tab-content.active').classList.remove('active');
    document.querySelector('.tab[data-tab="callLogs"]').classList.add('active');
    document.getElementById('callLogs').classList.add('active');
    saveState('callLogs');
}

function displayCallDetails(callId) {
    chrome.storage.local.get('callLogs', (result) => {
        const callLog = result.callLogs[callId];
        if (callLog) {
            const appointmentSet = callLog.calendarLink ? "Yes" : "No";
            const calendarLink = callLog.calendarLink ? `<a href="${callLog.calendarLink}" target="_blank">Google Calendar Link</a>` : "No appointment set";

            document.getElementById('callDetailsContainer').innerHTML = `
                <audio controls>
                    <source src="${callLog.recordingUrl}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
                <p><strong>Description of Issue:</strong> ${callLog.issueDescription}</p>
                <p><strong>Potential Prices:</strong> ${callLog.prices}</p>
                <p><strong>Appointment Set:</strong> ${appointmentSet}</p>
                <p>${calendarLink}</p>
            `;
            document.getElementById('callDetailsModal').style.display = 'flex';
        }
    });
}

// Event listener for closing the modal
document.querySelectorAll('.close').forEach(closeButton => {
    closeButton.addEventListener('click', () => {
        closeButton.closest('.modal').style.display = 'none';
    });
});





// const TWILIO_ACCOUNT_SID = 'ACfbd0b087e41fd42be2593fafbf8cc56f';
// const TWILIO_AUTH_TOKEN = 'b1009be1aed2f34db2b8167050e74b4a';

// document.addEventListener('DOMContentLoaded', () => {
//     console.log('DOM loaded');
//     restoreState();

//     // Automatic sign-in
//     chrome.identity.getAuthToken({ interactive: false }, (token) => {
//         if (token) {
//             authenticateUser(token);
//         } else {
//             document.getElementById('signInButton').style.display = 'block';
//         }
//     });

//     document.getElementById('signInButton').addEventListener('click', () => {
//         console.log('Sign in button clicked');
//         chrome.identity.getAuthToken({ interactive: true }, (token) => {
//             if (chrome.runtime.lastError) {
//                 console.error('Error getting auth token:', chrome.runtime.lastError);
//                 return;
//             }
//             authenticateUser(token);
//         });
//     });

    

//     document.getElementById('logout').addEventListener('click', () => {
//         chrome.identity.getAuthToken({ interactive: false }, (token) => {
//             if (token) {
//                 chrome.identity.removeCachedAuthToken({ token: token }, () => {
//                     console.log('Logged out');
//                     chrome.storage.local.remove('userInfo');
//                     checkLoginStatus();
//                 });
//             } else {
//                 console.error('No token found for removal');
//             }
//         });
//     });

    
//     document.getElementById('settings').addEventListener('click', () => {
//         document.getElementById('settingsModal').style.display = 'flex';
//     });

//     document.querySelectorAll('.close').forEach(closeButton => {
//         closeButton.addEventListener('click', () => {
//             closeButton.closest('.modal').style.display = 'none';
//         });
//     });

//     document.getElementById('toggleTheme').addEventListener('change', (event) => {
//         document.body.classList.toggle('light-mode', event.target.checked);
//     });

//     checkLoginStatus();
//     fetchCallLogs();
// });

// async function fetchCallLogs() {
//     try {
//         const response = await fetch('http://localhost:5000/fetch-call-logs');
//         const data = await response.json();

//         if (response.ok) {
//             const callLogsContainer = document.getElementById('callLogsContainer');
//             if (callLogsContainer) {
//                 callLogsContainer.innerHTML = ''; // Clear previous logs

//                 data.forEach((call, index) => {
//                     const callElement = document.createElement('div');
//                     callElement.className = 'call-log';
//                     callElement.dataset.callId = index;

//                     const from = call.from || 'Unknown';
//                     const startTime = call.start_time || call.date_created || call.date_updated || 'Unknown';
//                     const formattedStartTime = formatCallTime(startTime);

//                     callElement.innerHTML = `
//                         <p style="font-size: 22px"><strong></strong> ${from}</p>
//                         <p style="font-size: 22px">${formattedStartTime}</p>
//                     `;

//                     callLogsContainer.appendChild(callElement);
//                 });

//                 // Add event listener for call log clicks
//                 callLogsContainer.addEventListener('click', function(event) {
//                     if (event.target && event.target.closest('.call-log')) {
//                         displayCallDetails(event.target.closest('.call-log').dataset.callId);
//                     }
//                 });
//             } else {
//                 console.error('Error: callLogsContainer element not found.');
//             }
//         } else {
//             console.error('Unexpected response format:', data);
//             alert(`Error fetching call logs: ${data.error}`);
//         }
//     } catch (error) {
//         console.error('Error fetching call logs:', error);
//         alert('Error fetching call logs');
//     }
// }

// function formatCallTime(dateString) {
//     const callDate = new Date(dateString);
//     if (isNaN(callDate.getTime())) {
//         return 'Invalid Date';
//     }

//     const options = { 
//         weekday: 'short', 
//         year: 'numeric', 
//         month: 'short', 
//         day: 'numeric', 
//         hour: '2-digit', 
//         minute: '2-digit' 
//     };
//     return callDate.toLocaleString('en-US', options);
// }

// function authenticateUser(token) {
//     fetch('http://localhost:5000/authenticate', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json',
//             'Authorization': 'Bearer ' + token
//         }
//     }).then(response => response.json())
//         .then(data => {
//             chrome.storage.local.get(['phoneNumber', 'recEmail'], (result) => {
//                 data.phone = result.phoneNumber || '';
//                 data.recemail = result.recEmail || '';
//                 chrome.storage.local.set({ userInfo: data }, () => {
//                     displayUserInfo(data);
//                 });
//             });
//         })
//         .catch(error => {
//             console.error('Error fetching user data:', error);
//         });
// }

// function displayUserInfo(data) {
//     document.getElementById('userPicture').src = data.picture;
//     document.getElementById('userPicture').style.display = 'block';
//     document.getElementById('signInButton').style.display = 'none';
// }

// function checkLoginStatus() {
//     chrome.storage.local.get('userInfo', (result) => {
//         if (result.userInfo) {
//             displayUserInfo(result.userInfo);
//         } else {
//             document.getElementById('signInButton').style.display = 'block';
//             document.getElementById('userPicture').style.display = 'none';
//         }
//     });
// }

// function saveState(state) {
//     chrome.storage.local.set({ currentState: state });
// }

// function restoreState() {
//     chrome.storage.local.get('currentState', (result) => {
//         if (result.currentState) {
//             showCallLogs();
//         } else {
//             showCallLogs();
//         }
//     });
// }

// function showCallLogs() {
//     document.querySelector('.tab.active').classList.remove('active');
//     document.querySelector('.tab-content.active').classList.remove('active');
//     document.querySelector('.tab[data-tab="callLogs"]').classList.add('active');
//     document.getElementById('callLogs').classList.add('active');
//     saveState('callLogs');
// }

// function displayCallDetails(callId) {
//     chrome.storage.local.get('callLogs', (result) => {
//         const callLog = result.callLogs[callId];
//         if (callLog) {
//             const appointmentSet = callLog.calendarLink ? "Yes" : "No";
//             const calendarLink = callLog.calendarLink ? `<a href="${callLog.calendarLink}" target="_blank">Google Calendar Link</a>` : "No appointment set";

//             document.getElementById('callDetailsContainer').innerHTML = `
//                 <audio controls>
//                     <source src="${callLog.recordingUrl}" type="audio/mpeg">
//                     Your browser does not support the audio element.
//                 </audio>
//                 <p><strong>Description of Issue:</strong> ${callLog.issueDescription}</p>
//                 <p><strong>Potential Prices:</strong> ${callLog.prices}</p>
//                 <p><strong>Appointment Set:</strong> ${appointmentSet}</p>
//                 <p>${calendarLink}</p>
//             `;
//             document.getElementById('callDetailsModal').style.display = 'flex';
//         }
//     });
// }

// // Event listener for closing the modal
// document.querySelectorAll('.close').forEach(closeButton => {
//     closeButton.addEventListener('click', () => {
//         closeButton.closest('.modal').style.display = 'none';
//     });
// });
document.addEventListener('DOMContentLoaded', () => {
    const signInButton = document.getElementById('signInButton');
    signInButton.addEventListener('click', () => {
      chrome.runtime.sendMessage({ type: 'signIn' }, response => {
        if (response.error) {
          console.error('Sign-in error:', response.error);
          alert('Sign-in error: ' + response.error);
        } else {
          console.log('User signed in successfully');
        }
      });
    });
  });
  
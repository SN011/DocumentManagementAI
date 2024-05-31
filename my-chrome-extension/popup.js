document.getElementById('sendCredentials').addEventListener('click', function() {
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    fetch('http://localhost:5000/set_credentials', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, email, phone })
    })
    .then(response => response.json())
    .then(data => {
        alert('Credentials sent successfully.');
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

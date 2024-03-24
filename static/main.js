document.getElementById('connect-slack').addEventListener('click', function() {
    window.location.href = '/auth/slack';
});

document.getElementById('summarize-slack').addEventListener('click', function() {
    fetch('/summarize')
        .then(response => response.json())
        .then(data => {
            console.log(data);
            // Display your summary data here
        });
});

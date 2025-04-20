document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Copy code button functionality
    const copyButtons = document.querySelectorAll('.copy-btn');
    
    copyButtons.forEach(button => {
        button.addEventListener('click', () => {
            const codeBlock = button.closest('.code-block').querySelector('pre');
            const codeToCopy = codeBlock.textContent;
            
            navigator.clipboard.writeText(codeToCopy).then(() => {
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                button.classList.add('btn-success');
                button.classList.remove('btn-secondary');
                
                setTimeout(() => {
                    button.textContent = originalText;
                    button.classList.remove('btn-success');
                    button.classList.add('btn-secondary');
                }, 2000);
            });
        });
    });

    // Example live endpoint testing
    const testEndpointButtons = document.querySelectorAll('.test-endpoint');
    
    testEndpointButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const endpoint = button.dataset.endpoint;
            const resultContainer = document.getElementById(button.dataset.target);
            
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
            
            try {
                const response = await fetch(endpoint);
                const data = await response.json();
                
                // Format the JSON response
                const jsonStr = JSON.stringify(data, null, 2);
                resultContainer.innerHTML = `<pre>${jsonStr}</pre>`;
                resultContainer.style.display = 'block';
            } catch (error) {
                resultContainer.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
                resultContainer.style.display = 'block';
            } finally {
                button.disabled = false;
                button.textContent = 'Test Endpoint';
            }
        });
    });
});

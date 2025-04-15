document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.querySelector('.drop-zone');
    const input = document.querySelector('.drop-zone__input');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');

    function handleFileSelect(file) {
        if (file && isValidFileType(file)) {
            updateThumbnail(file);
            uploadFile(file);
        } else {
            alert('Please upload an image file (PNG, JPG, JPEG, or GIF)');
        }
    }

    function isValidFileType(file) {
        const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/jpg'];
        return validTypes.includes(file.type);
    }

    function updateThumbnail(file) {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            dropZone.style.backgroundImage = `url('${reader.result}')`;
            dropZone.style.backgroundSize = 'cover';
            dropZone.style.backgroundPosition = 'center';
            dropZone.querySelector('.drop-zone__prompt').style.display = 'none';
        };
    }

    function clearResults() {
        // Reset the drop zone
        dropZone.style.backgroundImage = '';
        dropZone.style.backgroundSize = '';
        dropZone.style.backgroundPosition = '';
        dropZone.querySelector('.drop-zone__prompt').style.display = 'flex';
        
        // Clear the file input
        input.value = '';
        
        // Hide results
        results.classList.add('hidden');
        
        // Clear results content
        document.getElementById('productInfo').innerHTML = '';
        document.getElementById('priceComparison').innerHTML = '';
        document.getElementById('sentimentAnalysis').innerHTML = '';
    }

    function reanalyze() {
        if (input.files.length > 0) {
            handleFileSelect(input.files[0]);
        } else {
            alert('Please upload an image first');
        }
    }

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        loading.classList.remove('hidden');
        results.classList.add('hidden');

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            displayResults(data);
            loading.classList.add('hidden');
            results.classList.remove('hidden');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while processing your image. Please try again.');
            loading.classList.add('hidden');
        });
    }

    function displayResults(data) {
        const productInfo = document.getElementById('productInfo');
        const priceComparison = document.getElementById('priceComparison');
        const sentimentAnalysis = document.getElementById('sentimentAnalysis');

        // Display product info and action buttons
        productInfo.innerHTML = `
            <h2>${data.product}</h2>
            <p>Price comparison and analysis results</p>
            <div class="action-buttons">
                <button onclick="window.reanalyze()" class="action-button reanalyze">Reanalyze</button>
                <button onclick="window.clearResults()" class="action-button clear">Clear</button>
            </div>
        `;

        // Display price comparison
        priceComparison.innerHTML = data.prices
            .map(item => `
                <div class="price-card">
                    <span class="price-card__site">${item.site}</span>
                    <span class="price-card__price">$${item.price.toFixed(2)}</span>
                    <span class="price-card__rating">★ ${item.rating.toFixed(1)}</span>
                </div>
            `).join('');

        // Display sentiment analysis
        const sentimentScore = (data.sentiment.score * 100).toFixed(1);
        const sentimentColor = sentimentScore > 70 ? '#4CAF50' : 
                             sentimentScore > 40 ? '#FFC107' : '#F44336';

        sentimentAnalysis.innerHTML = `
            <div class="sentiment-analysis">
                <div class="sentiment-score" style="color: ${sentimentColor}">
                    Customer Satisfaction: ${sentimentScore}%
                </div>
                <div class="reviews">
                    ${data.sentiment.reviews.map(review => `
                        <div class="review">${review}</div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Make functions available globally for button clicks
    window.clearResults = clearResults;
    window.reanalyze = reanalyze;

    // Event Listeners
    dropZone.addEventListener('click', () => input.click());

    input.addEventListener('change', () => {
        if (input.files.length) {
            handleFileSelect(input.files[0]);
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drop-zone--over');
    });

    ['dragleave', 'dragend'].forEach(type => {
        dropZone.addEventListener(type, () => {
            dropZone.classList.remove('drop-zone--over');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drop-zone--over');

        if (e.dataTransfer.files.length) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
});
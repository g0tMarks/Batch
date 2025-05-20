/**
 * Utility functions for handling file downloads
 */

/**
 * Shows the download modal for a specific file
 * @param {string} filename - The name of the file to download
 */
function showDownloadModal(filename) {
    const modal = new bootstrap.Modal(document.getElementById('downloadModal'));
    const downloadButton = document.getElementById('downloadButton');
    
    // Clear any previous value
    document.getElementById('downloadPath').value = '';
    
    downloadButton.onclick = async function() {
        const customPath = document.getElementById('downloadPath').value;
        modal.hide();
        // Start download immediately after modal is hidden
        await downloadFile(filename, customPath);
    };
    
    modal.show();
}

/**
 * Downloads a file from the server
 * @param {string} filename - The name of the file to download
 * @param {string} customPath - Optional custom download path
 */
async function downloadFile(filename, customPath = null) {
    const url = customPath 
        ? `/download/${filename}?path=${encodeURIComponent(customPath)}`
        : `/download/${filename}`;
    
    try {
        // First check if the file exists and is accessible
        const checkResponse = await fetch(url, { method: 'HEAD' });
        if (!checkResponse.ok) {
            const error = await checkResponse.json();
            throw new Error(error.error || 'File not found');
        }

        // If file exists, trigger download using window.location
        window.location.href = url;
        
    } catch (error) {
        console.error('Download failed:', error);
        alert('Failed to download file: ' + error.message);
    }
}

/**
 * Creates a download button element
 * @param {string} filename - The name of the file to download
 * @returns {HTMLElement} - The download button element
 */
function createDownloadButton(filename) {
    const button = document.createElement('button');
    button.className = 'btn btn-primary btn-sm';
    button.textContent = 'Download';
    button.onclick = () => showDownloadModal(filename);
    return button;
}

/**
 * Creates a download link element
 * @param {string} filename - The name of the file to download
 * @param {string} text - Optional text for the link (defaults to filename)
 * @returns {HTMLElement} - The download link element
 */
function createDownloadLink(filename, text = null) {
    const link = document.createElement('a');
    link.href = '#';
    link.textContent = text || filename;
    link.onclick = (e) => {
        e.preventDefault();
        showDownloadModal(filename);
    };
    return link;
}

/**
 * Loads recent reports and displays them in a container
 * @param {string} containerId - The ID of the container to display reports in
 */
async function loadRecentReports(containerId) {
    try {
        const response = await fetch('/reports');
        const reports = await response.json();
        
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        
        reports.forEach(report => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            item.innerHTML = `
                <div>
                    <h5 class="mb-1">${report.filename}</h5>
                    <small class="text-muted">Generated: ${new Date(report.created_at).toLocaleString()}</small>
                </div>
            `;
            item.appendChild(createDownloadButton(report.filename));
            container.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading reports:', error);
    }
}

// Export functions for use in other files
export {
    showDownloadModal,
    downloadFile,
    createDownloadButton,
    createDownloadLink,
    loadRecentReports
}; 
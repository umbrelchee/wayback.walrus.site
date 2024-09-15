let currentPage = 1;

document.getElementById('archiveForm').addEventListener('submit', async function (event) {
    event.preventDefault();
    document.getElementById('spinner').style.display = 'block';
    const url = document.getElementById('url').value;

    try {
        const formData = new FormData();
        formData.append('url', url);
        const response = await fetch('/archive', {
            method: 'POST',
            body: formData
        });

        if (response.redirected) {
            window.location.href = response.url;
        } else {
            alert('Archiving failed.');
        }
    } catch (error) {
        alert('An error occurred while archiving.');
    } finally {
        document.getElementById('spinner').style.display = 'none';
    }
});

async function loadTable(page) {
    try {
        const response = await fetch(`/archives?page=${page}`);
        const data = await response.json();

        const tableBody = document.getElementById('tableBody');
        tableBody.innerHTML = '';

        data.rows.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${row.date}</td>
                <td>${row.url}</td>
                <td><a href="#" onclick="loadBlobAndOpen('${row.blobUrl}'); return false;">📄</a></td>
            `;
            tableBody.appendChild(tr);
        });

        document.getElementById('pageNumber').textContent = `Page ${data.currentPage} of ${data.totalPages}`;
        document.getElementById('prevPage').disabled = data.currentPage === 1;
        document.getElementById('nextPage').disabled = data.currentPage === data.totalPages;
    } catch (error) {
        console.error('Error loading table:', error);
    }
}

function changePage(direction) {
    currentPage += direction;
    loadTable(currentPage);
}

async function loadBlobAndOpen(blobUrl) {
    try {
        const response = await fetch(blobUrl);

        if (!response.ok) {
            throw new Error('Failed to fetch file:', response.status);
        }

        const blob = await response.blob();
        const reader = new FileReader();

        reader.onload = function (event) {
            const htmlContent = event.target.result;
            const newTab = window.open();
            newTab.document.write(htmlContent);
            newTab.document.close();
        };
        reader.readAsText(blob);
    } catch (error) {
        console.error('Error opening blob:', error);
    }
}

// Load the initial table
loadTable(currentPage);

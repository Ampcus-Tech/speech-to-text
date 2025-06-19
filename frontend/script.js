document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const serviceSelect = document.getElementById('service-select');
    const recordBtns = document.querySelectorAll('.record-btn');
    const nameField = document.getElementById('name-field');
    const expField = document.getElementById('exp-field');
    const designationField = document.getElementById('designation-field');
    const addressField = document.getElementById('address-field');
    const emailField = document.getElementById('email-field');
    const submitBtn = document.getElementById('submit-btn');
    const resetBtn = document.getElementById('reset-btn');
    const confirmationModal = document.getElementById('confirmation-modal');
    const confirmName = document.getElementById('confirm-name');
    const confirmExp = document.getElementById('confirm-exp');
    const confirmDesignation = document.getElementById('confirm-designation');
    const confirmAddress = document.getElementById('confirm-address');
    const confirmEmail = document.getElementById('confirm-email');
    const confirmBtn = document.getElementById('confirm-btn');
    const editBtn = document.getElementById('edit-btn');
    const toggleRecordsBtn = document.getElementById('toggle-records-btn');
    const recordsSection = document.querySelector('.records-section');
    const recordsBody = document.getElementById('records-body');
    const editModal = document.getElementById('edit-modal');
    const editForm = document.getElementById('edit-form');
    const editId = document.getElementById('edit-id');
    const editName = document.getElementById('edit-name');
    const editExp = document.getElementById('edit-exp');
    const editDesignation = document.getElementById('edit-designation');
    const editAddress = document.getElementById('edit-address');
    const editEmail = document.getElementById('edit-email');
    const cancelEdit = document.getElementById('cancel-edit');
    const statusBar = document.getElementById('status-bar');
    const statusText = document.getElementById('status-text');
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');
    
    // Transcript elements
    const nameTranscript = document.getElementById('name-transcript');
    const expTranscript = document.getElementById('exp-transcript');
    const designationTranscript = document.getElementById('designation-transcript');
    const addressTranscript = document.getElementById('address-transcript');
    const emailTranscript = document.getElementById('email-transcript');
    
    // Pagination variables
    const recordsPerPage = 5;
    let currentPage = 1;
    let totalPages = 1;
    let allRecords = [];
    let filteredRecords = [];
    
    // Recording state
    let isRecording = false;
    let currentRecordingBtn = null;
    
    // Initialize
    updateStatus('Ready to record. Select a field and click Record.');
    
    // Event Listeners
    recordBtns.forEach(btn => {
        btn.addEventListener('click', async function() {
            if (isRecording) return;
            
            const field = this.dataset.field;
            const service = serviceSelect.value;
            
            if (!service) {
                updateStatus('Please select a speech recognition service first.', 'error');
                return;
            }
            
            isRecording = true;
            currentRecordingBtn = this;
            
            // Update UI
            this.classList.add('recording');
            this.innerHTML = '<i class="fas fa-circle"></i> Recording...';
            updateStatus(`Recording for ${field.replace('_', ' ')}...`);
            
            try {
                const response = await fetch(
                    `http://localhost:8004/transcribe-field?service=${service}&field=${field}`, 
                    { method: 'POST' }
                );
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `Server error: ${response.status}`);
                }
                
                const data = await response.json();
                updateField(field, data.value);
                updateTranscript(field, data.transcript);
                updateStatus(`Successfully captured ${field.replace('_', ' ')}`, 'success');
            } catch (err) {
                updateStatus(`Error: ${err.message}`, 'error');
                console.error(err);
            } finally {
                isRecording = false;
                if (currentRecordingBtn) {
                    currentRecordingBtn.classList.remove('recording');
                    currentRecordingBtn.innerHTML = '<i class="fas fa-microphone"></i> Record';
                    currentRecordingBtn = null;
                }
            }
        });
    });
    
    submitBtn.addEventListener('click', () => {
        // Validate form
        if (!nameField.value || !emailField.value) {
            updateStatus('Name and email are required fields', 'error');
            return;
        }
        
        // Show confirmation modal
        confirmName.textContent = nameField.value;
        confirmExp.textContent = expField.value || '0';
        confirmDesignation.textContent = designationField.value || 'Not provided';
        confirmAddress.textContent = addressField.value || 'Not provided';
        confirmEmail.textContent = emailField.value;
        
        confirmationModal.style.display = 'flex';
    });
    
    confirmBtn.addEventListener('click', async () => {
        confirmationModal.style.display = 'none';
        updateStatus('Creating record...');
        
        try {
            const record = {
                candidate_name: nameField.value,
                years_of_experience: expField.value || '0',
                current_designation: designationField.value,
                address: addressField.value,
                email: emailField.value
            };
            
            const response = await fetch('http://localhost:8004/create-record', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(record)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }
            
            const data = await response.json();
            updateStatus(`Record created successfully! ID: ${data.id}`, 'success');
            resetForm();
            // Refresh records if visible
            if (recordsSection.style.display === 'block') {
                loadRecords();
            }
        } catch (err) {
            updateStatus(`Error: ${err.message}`, 'error');
        }
    });
    
    editBtn.addEventListener('click', () => {
        confirmationModal.style.display = 'none';
    });
    
    resetBtn.addEventListener('click', resetForm);
    
    toggleRecordsBtn.addEventListener('click', () => {
        if (recordsSection.style.display === 'block') {
            recordsSection.style.display = 'none';
            toggleRecordsBtn.textContent = 'Show Records';
        } else {
            recordsSection.style.display = 'block';
            toggleRecordsBtn.textContent = 'Hide Records';
            loadRecords();
        }
    });
    
    editForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const recordId = editId.value;
        const recordData = {
            candidate_name: editName.value,
            years_of_experience: editExp.value,
            current_designation: editDesignation.value,
            address: editAddress.value,
            email: editEmail.value
        };
        
        updateStatus('Updating record...');
        
        try {
            const response = await fetch(`http://localhost:8004/update-record/${recordId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(recordData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }
            
            updateStatus('Record updated successfully!', 'success');
            editModal.style.display = 'none';
            loadRecords();
        } catch (err) {
            updateStatus(`Error: ${err.message}`, 'error');
        }
    });
    
    cancelEdit.addEventListener('click', () => {
        editModal.style.display = 'none';
    });
    
    searchBtn.addEventListener('click', loadRecords);
    searchInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') loadRecords();
    });
    
    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderRecords();
        }
    });
    
    nextPageBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderRecords();
        }
    });
    
    // Functions
    function updateField(field, value) {
        switch (field) {
            case 'candidate_name':
                nameField.value = value;
                break;
            case 'years_of_experience':
                expField.value = value;
                break;
            case 'current_designation':
                designationField.value = value;
                break;
            case 'address':
                addressField.value = value;
                break;
            case 'email':
                emailField.value = value;
                break;
        }
    }
    
    function updateTranscript(field, transcript) {
        if (!transcript) return;
        
        switch (field) {
            case 'candidate_name':
                nameTranscript.textContent = `Transcript: ${transcript}`;
                nameTranscript.style.display = 'block';
                break;
            case 'years_of_experience':
                expTranscript.textContent = `Transcript: ${transcript}`;
                expTranscript.style.display = 'block';
                break;
            case 'current_designation':
                designationTranscript.textContent = `Transcript: ${transcript}`;
                designationTranscript.style.display = 'block';
                break;
            case 'address':
                addressTranscript.textContent = `Transcript: ${transcript}`;
                addressTranscript.style.display = 'block';
                break;
            case 'email':
                emailTranscript.textContent = `Transcript: ${transcript}`;
                emailTranscript.style.display = 'block';
                break;
        }
    }
    
    function resetForm() {
        nameField.value = '';
        expField.value = '';
        designationField.value = '';
        addressField.value = '';
        emailField.value = '';
        
        // Hide transcripts
        nameTranscript.style.display = 'none';
        expTranscript.style.display = 'none';
        designationTranscript.style.display = 'none';
        addressTranscript.style.display = 'none';
        emailTranscript.style.display = 'none';
        
        updateStatus('Form has been reset');
    }
    
    async function loadRecords() {
        updateStatus('Loading records...');
        
        try {
            const response = await fetch('http://localhost:8004/records');
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }
            
            allRecords = await response.json();
            applySearchFilter();
            calculatePagination();
            renderRecords();
            updateStatus(`Loaded ${allRecords.length} records`, 'success');
        } catch (err) {
            updateStatus(`Error: ${err.message}`, 'error');
        }
    }
    
    function applySearchFilter() {
        const searchTerm = searchInput.value.toLowerCase();
        
        if (!searchTerm) {
            filteredRecords = [...allRecords];
            return;
        }
        
        filteredRecords = allRecords.filter(record => 
            record.candidate_name.toLowerCase().includes(searchTerm) ||
            (record.current_designation && record.current_designation.toLowerCase().includes(searchTerm)) ||
            (record.address && record.address.toLowerCase().includes(searchTerm)) ||
            record.email.toLowerCase().includes(searchTerm)
        );
    }
    
    function calculatePagination() {
        totalPages = Math.ceil(filteredRecords.length / recordsPerPage);
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        
        prevPageBtn.disabled = currentPage === 1;
        nextPageBtn.disabled = currentPage === totalPages || totalPages === 0;
    }
    
    function renderRecords() {
        recordsBody.innerHTML = '';
        calculatePagination();
        
        if (filteredRecords.length === 0) {
            recordsBody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No records found</td></tr>';
            return;
        }
        
        const startIndex = (currentPage - 1) * recordsPerPage;
        const endIndex = Math.min(startIndex + recordsPerPage, filteredRecords.length);
        const pageRecords = filteredRecords.slice(startIndex, endIndex);
        
        pageRecords.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.id.substring(0, 6)}</td>
                <td>${record.candidate_name}</td>
                <td>${record.years_of_experience}</td>
                <td>${record.current_designation || '-'}</td>
                <td>${record.address || '-'}</td>
                <td>${record.email}</td>
                <td>${record.date}</td>
                <td>
                    <button class="action-btn edit-btn" data-id="${record.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            `;
            recordsBody.appendChild(row);
        });
        
        // Add event listeners to edit buttons
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', async function() {
                const recordId = this.dataset.id;
                updateStatus(`Loading record ${recordId}...`);
                
                try {
                    const response = await fetch(`http://localhost:8004/record/${recordId}`);
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || `Server error: ${response.status}`);
                    }
                    
                    const record = await response.json();
                    
                    // Populate edit form
                    editId.value = record.id;
                    editName.value = record.candidate_name;
                    editExp.value = record.years_of_experience;
                    editDesignation.value = record.current_designation || '';
                    editAddress.value = record.address || '';
                    editEmail.value = record.email;
                    
                    // Show edit modal
                    editModal.style.display = 'flex';
                    updateStatus(`Record ${recordId} loaded for editing`);
                } catch (err) {
                    updateStatus(`Error: ${err.message}`, 'error');
                }
            });
        });
    }
    
    function updateStatus(message, type = 'info') {
        statusText.textContent = message;
        
        // Clear previous classes
        statusBar.className = 'status-bar';
        
        // Add type-specific class
        if (type === 'error') {
            statusBar.classList.add('error');
        } else if (type === 'success') {
            statusBar.classList.add('success');
        } else if (type === 'warning') {
            statusBar.classList.add('warning');
        }
    }
    
    // ... (existing code) ...

// In updateField function:
function updateField(field, value) {
    console.log(`Updating ${field} with value: ${value}`); // Debug logging
    
    switch (field) {
        case 'candidate_name':
            nameField.value = value;
            break;
        case 'years_of_experience':
            expField.value = value; // Fixed field mapping
            break;
        case 'current_designation':
            designationField.value = value;
            break;
        case 'address':
            addressField.value = value;
            break;
        case 'email':
            emailField.value = value;
            break;
    }
}

// In renderRecords function:
function renderRecords() {
    // ... (existing code) ...
    
    pageRecords.forEach(record => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${record.id.substring(0, 6)}</td>
            <td><input type="text" class="editable" data-field="candidate_name" data-id="${record.id}" value="${record.candidate_name}"></td>
            <td><input type="number" class="editable" data-field="years_of_experience" data-id="${record.id}" value="${record.years_of_experience}" min="0"></td>
            <td><input type="text" class="editable" data-field="current_designation" data-id="${record.id}" value="${record.current_designation || ''}"></td>
            <td><input type="text" class="editable" data-field="address" data-id="${record.id}" value="${record.address || ''}"></td>
            <td><input type="email" class="editable" data-field="email" data-id="${record.id}" value="${record.email}"></td>
            <td>${record.date}</td>
            <td>
                <button class="action-btn save-btn" data-id="${record.id}">
                    <i class="fas fa-save"></i>
                </button>
                <button class="action-btn delete-btn" data-id="${record.id}">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        recordsBody.appendChild(row);
    });
    
    // Add event listeners to save buttons
    document.querySelectorAll('.save-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const recordId = this.dataset.id;
            const row = this.closest('tr');
            const inputs = row.querySelectorAll('.editable');
            
            const updateData = {};
            inputs.forEach(input => {
                updateData[input.dataset.field] = input.value;
            });
            
            updateStatus(`Saving record ${recordId}...`);
            
            try {
                const response = await fetch(`http://localhost:8004/update-record/${recordId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updateData)
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `Server error: ${response.status}`);
                }
                
                updateStatus('Record updated successfully!', 'success');
                // Refresh records if needed
                loadRecords();
            } catch (err) {
                updateStatus(`Error: ${err.message}`, 'error');
            }
        });
    });
    
    // Add event listeners to delete buttons
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const recordId = this.dataset.id;
            if (confirm(`Are you sure you want to delete record ${recordId.substring(0, 6)}?`)) {
                updateStatus(`Deleting record ${recordId}...`);
                
                try {
                    // This would require a DELETE endpoint in backend
                    // For now, we'll use update to mark as deleted
                    const response = await fetch(`http://localhost:8004/update-record/${recordId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ deleted: true })
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || `Server error: ${response.status}`);
                    }
                    
                    updateStatus('Record marked as deleted!', 'success');
                    loadRecords();
                } catch (err) {
                    updateStatus(`Error: ${err.message}`, 'error');
                }
            }
        });
    });
}

// ... (rest of the code) ...

    // Close modals when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === confirmationModal) {
            confirmationModal.style.display = 'none';
        }
        if (e.target === editModal) {
            editModal.style.display = 'none';
        }
    });
});
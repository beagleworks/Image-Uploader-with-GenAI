document.addEventListener('DOMContentLoaded', function() {
    loadImages();
    
    document.getElementById('uploadForm').addEventListener('submit', function(e) {
        e.preventDefault();
        uploadImage();
    });
    
    document.getElementById('resetBtn').addEventListener('click', function() {
        resetDatabase();
    });
    
    // Modal functionality
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const modalCaption = document.getElementById('modalCaption');
    const closeBtn = document.getElementsByClassName('close-modal')[0];
    
    // Close modal when clicking the close button
    closeBtn.onclick = function() {
        modal.style.display = 'none';
    }
    
    // Close modal when clicking outside the image
    modal.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    }
    
    // Close modal when pressing Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && modal.style.display === 'block') {
            modal.style.display = 'none';
        }
    });
});

function uploadImage() {
    const formData = new FormData();
    const imageInput = document.getElementById('imageInput');
    const commentInput = document.getElementById('commentInput');
    
    if (!imageInput.files[0]) {
        showMessage('画像を選択してください', 'error');
        return;
    }
    
    formData.append('image', imageInput.files[0]);
    formData.append('comment', commentInput.value);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            showMessage(data.message, 'success');
            loadImages();
            imageInput.value = '';
            commentInput.value = '';
        } else {
            showMessage(data.error, 'error');
        }
    })
    .catch(error => {
        showMessage('アップロードに失敗しました', 'error');
    });
}

function loadImages() {
    fetch('/images')
    .then(response => response.json())
    .then(images => {
        const imageList = document.getElementById('imageList');
        imageList.innerHTML = '';
        images.forEach(img => {
            console.log('Loading image:', img.filename, 'Generated image:', img.generated_image);
            const item = document.createElement('div');
            item.className = 'image-item';
            item.innerHTML = `
                <img src="/uploads/${encodeURIComponent(img.filename)}" alt="Uploaded image" onclick="openModal('/uploads/${encodeURIComponent(img.filename)}', 'アップロード画像')" onerror="handleImageError(this)">
                <div class="image-info">
                    <p><strong>コメント:</strong> <span id="comment-${img.filename}">${img.comment}</span></p>
                    <div class="button-group">
                        <button class="edit-btn" onclick="editComment('${img.filename}')">✏️ 編集</button>
                        <button class="generate-btn" onclick="generateResponse('${img.filename}', '${img.comment}')">🤖 AI</button>
                        <button class="delete-btn" onclick="deleteImage('${img.filename}')">削除</button>
                    </div>
                    ${img.generated_image ? `<div class="ai-generated-section">
                        <h4>🎨 Gemini 2.5 Flash Image (Nano Banana)生成結果</h4>
                        <img src="/generated/${encodeURIComponent(img.generated_image)}" alt="Generated image" class="generated-image" onclick="openModal('/generated/${encodeURIComponent(img.generated_image)}', 'AI生成画像')" onerror="handleImageError(this)">
                    </div>` : ''}
                </div>
            `;
            imageList.appendChild(item);
        });
    })
    .catch(error => {
        console.error('Error loading images:', error);
        showMessage('画像の読み込みに失敗しました', 'error');
    });
}

function generateResponse(filename, comment) {
    // Don't pass comment from frontend, let backend get the latest from database
    fetch('/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ filename: filename })
    })
    .then(response => response.json())
    .then(data => {
        if (data.generated_image) {
            showMessage('🎨 Gemini 2.5 Flash Image (Nano Banana) 生成が完了しました！', 'success');
            loadImages(); // Reload to show the generated image
        } else {
            showMessage(data.error, 'error');
        }
    })
    .catch(error => {
        showMessage('🎨 Gemini 2.5 Flash Image (Nano Banana)生成に失敗しました', 'error');
    });
}

function openModal(imageSrc, caption) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const modalCaption = document.getElementById('modalCaption');
    
    modal.style.display = 'block';
    modalImg.src = imageSrc;
    modalCaption.innerHTML = caption;
}

function resetDatabase() {
    if (confirm('⚠️ 警告: この操作はすべての画像とデータを削除します。本当にリセットしますか？\n\nこの操作は取り消すことができません。')) {
        if (confirm('最終確認: すべてのデータが失われます。よろしいですか？')) {
            fetch('/reset', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    showMessage('✅ データベースがリセットされました', 'success');
                    loadImages(); // Reload to show empty list
                } else {
                    showMessage(data.error, 'error');
                }
            })
            .catch(error => {
                showMessage('❌ リセットに失敗しました', 'error');
            });
        }
    }
}

function showMessage(message, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = message;
    messageDiv.className = type;
    setTimeout(() => {
        messageDiv.textContent = '';
        messageDiv.className = '';
    }, 5000);
}

function deleteImage(filename) {
    if (confirm('この画像を削除しますか？')) {
        fetch(`/delete/${filename}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                showMessage(data.message, 'success');
                loadImages();
            } else {
                showMessage(data.error, 'error');
            }
        })
        .catch(error => {
            showMessage('削除に失敗しました', 'error');
        });
    }
}

function editComment(filename) {
    const commentSpan = document.getElementById(`comment-${filename}`);
    const currentComment = commentSpan.textContent;
    
    // Create input field
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentComment;
    input.className = 'edit-input';
    
    // Create save button
    const saveBtn = document.createElement('button');
    saveBtn.textContent = '保存';
    saveBtn.className = 'save-btn';
    saveBtn.onclick = function() {
        const newComment = input.value.trim();
        if (newComment && newComment !== currentComment) {
            fetch(`/edit_comment/${filename}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ comment: newComment })
            })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    commentSpan.textContent = newComment;
                    showMessage('コメントが更新されました', 'success');
                } else {
                    showMessage(data.error, 'error');
                }
            })
            .catch(error => {
                showMessage('コメントの更新に失敗しました', 'error');
            });
        }
        // Restore original display
        commentSpan.textContent = currentComment;
    };
    
    // Create cancel button
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'キャンセル';
    cancelBtn.className = 'cancel-btn';
    cancelBtn.onclick = function() {
        commentSpan.textContent = currentComment;
    };
    
    // Replace comment with input and buttons
    commentSpan.innerHTML = '';
    commentSpan.appendChild(input);
    commentSpan.appendChild(saveBtn);
    commentSpan.appendChild(cancelBtn);
    
    input.focus();
}

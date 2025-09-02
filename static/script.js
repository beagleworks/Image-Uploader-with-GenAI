document.addEventListener('DOMContentLoaded', function() {
    loadImages();
    
    document.getElementById('uploadForm').addEventListener('submit', function(e) {
        e.preventDefault();
        uploadImage();
    });
    
    document.getElementById('resetBtn').addEventListener('click', function() {
        resetDatabase();
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
                <img src="/uploads/${encodeURIComponent(img.filename)}" alt="Uploaded image" onerror="handleImageError(this)">
                <div class="image-info">
                    <p><strong>コメント:</strong> ${img.comment}</p>
                    <div class="button-group">
                        <button class="generate-btn" onclick="generateResponse('${img.filename}', '${img.comment}')">🤖 AI</button>
                        <button class="delete-btn" onclick="deleteImage('${img.filename}')">削除</button>
                    </div>
                    ${img.generated_image ? `<div class="ai-generated-section">
                        <h4>🎨 Gemini 2.5 Flash Image生成結果</h4>
                        <img src="/generated/${encodeURIComponent(img.generated_image)}" alt="Generated image" class="generated-image" onerror="handleImageError(this)">
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
    fetch('/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ filename: filename, comment: comment })
    })
    .then(response => response.json())
    .then(data => {
        if (data.generated_image) {
            showMessage('🎨 Gemini 2.5 Flash Image生成が完了しました！', 'success');
            loadImages(); // Reload to show the generated image
        } else {
            showMessage(data.error, 'error');
        }
    })
    .catch(error => {
        showMessage('🎨 Gemini 2.5 Flash Image生成に失敗しました', 'error');
    });
}

function handleImageError(img) {
    console.error('Image failed to load:', img.src);
    img.style.display = 'none';
    const errorDiv = document.createElement('div');
    errorDiv.className = 'image-error';
    errorDiv.innerHTML = '📷 画像の読み込みに失敗しました';
    img.parentNode.insertBefore(errorDiv, img);
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

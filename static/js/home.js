document.addEventListener("DOMContentLoaded", function () {
    const fileInput = document.querySelector(".parent input[type=file]");
    const previewImg = document.querySelector(".preview-img");
    const selectLabel = document.querySelector(".select");
    const TIMEOUT_DURATION = 1 * 60 * 1000;
    let timeout;

    function handleFile(file) {
        if (file) {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;

            const fileReader = new FileReader();
            fileReader.readAsDataURL(file);

            fileReader.onload = function (e) {
                const imgTag = document.createElement('img');
                imgTag.src = e.target.result;
                imgTag.alt = '選択された画像';

                previewImg.innerHTML = '';
                previewImg.appendChild(imgTag);

                imgTag.onload = function () {
                    const imgWidth = imgTag.naturalWidth;
                    const imgHeight = imgTag.naturalHeight;

                    if (imgWidth > 420 || imgHeight > 420) {
                        imgTag.style.width = '';
                        imgTag.style.height = '';
                    } else {
                        imgTag.style.width = `${imgWidth}px`;
                        imgTag.style.height = `${imgHeight}px`;
                    }
                };

                submitBtn.disabled = false;
            };

            fileReader.onerror = function () {
                previewImg.textContent = "ファイルの読み込みに失敗しました";
            };
        } else {
            previewImg.textContent = "選択されていません";
            previewImg.innerHTML = '';
            submitBtn.disabled = true;
        }
    }

    fileInput.addEventListener("change", function (event) {
        handleFile(event.target.files[0]);
    });

    selectLabel.addEventListener("dragover", function (event) {
        event.preventDefault();
        selectLabel.classList.add("drag-over");
    });

    selectLabel.addEventListener("dragleave", function () {
        selectLabel.classList.remove("drag-over");
    });

    selectLabel.addEventListener("drop", function (event) {
        event.preventDefault();
        selectLabel.classList.remove("drag-over");
        const files = event.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith("image/")) {
            const errorMessageElement = document.querySelector(".error-message");
            if (errorMessageElement) {
                errorMessageElement.textContent = "";
            }
            handleFile(files[0]);
        } else {
            let errorMessageElement = document.querySelector(".error-message");
            if (!errorMessageElement) {
                errorMessageElement = document.createElement("div");
                errorMessageElement.className = "error-message";
                errorMessageElement.style.color = "red";
                selectLabel.parentNode.insertBefore(errorMessageElement, selectLabel.nextSibling);
            }
            errorMessageElement.textContent = "画像ファイルのみ選択可能です";
            setTimeout(function () {
                errorMessageElement.textContent = "";
            }, 3000);
        }
    });
    
    function resetTimeout() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            window.location.href = TIMEOUT_URL;
        }, TIMEOUT_DURATION);
    }

    document.addEventListener("mousemove", resetTimeout);
    document.addEventListener("keypress", resetTimeout);
    document.addEventListener("click", resetTimeout);
    document.addEventListener("scroll", resetTimeout);
});

function clearFile(event) {
    event.preventDefault();
    const form = document.querySelector("form");
    if (form) {
        form.reset();
    }
    const previewImg = document.querySelector(".preview-img");
    if (previewImg) {
        previewImg.innerHTML = '';
    }
}

window.onload = () => {
    const animatedElement = document.getElementById('animatedElement');
    animatedElement.classList.add('show');
    animatedElement.classList.add('fadeout', 'is-animated');
    animatedElement.addEventListener('animationend', () => {
        animatedElement.style.pointerEvents = 'none';
    });
};

document.getElementById('logoutBtn').addEventListener('click', function () {
    fetch('/home', { method: 'GET' })
        .then(response => {
            if (response.ok) {
                window.location.href = "/logout";
            } else {
                alert('ログアウトに失敗しました。もう一度試してください。');
            }
        })
        .catch(error => {
            console.error('ログアウト中にエラーが発生しました:', error);
        });
});
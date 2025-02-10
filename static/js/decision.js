document.addEventListener("DOMContentLoaded", function () {
    const imageElement = document.querySelector(".select-picture img");
    const TIMEOUT_DURATION = 1 * 60 * 1000;
    let timeout;


    function handleImageLoad(image) {
        if (image.naturalWidth > 400 || image.naturalHeight > 400) {
            image.style.width = '';
            image.style.height = '';
        } else {
            image.style.width = image.naturalWidth + 'px';
            image.style.height = image.naturalHeight + 'px';
        }
    }

    if (imageElement) {
        imageElement.addEventListener("load", function () {
            handleImageLoad(imageElement);
        });
        if (imageElement.complete) {
            imageElement.dispatchEvent(new Event("load"));
        }
    }

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

    resetTimeout();
});

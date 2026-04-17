/**
 * Opens the modal and sets the image source
 * @param {string} imgSrc - The filename of the certificate image
 */
function openModal(imgSrc) {
    const modal = document.getElementById("imageModal");
    const modalImg = document.getElementById("modalImage");

    if (modal && modalImg) {
        modal.style.display = "flex";
        modalImg.src = encodeURI(imgSrc);
        document.body.style.overflow = "hidden";
    }
}

function closeModal() { 
    const modal = document.getElementById("imageModal");

    if (modal) {
        modal.style.display = "none";
        document.body.style.overflow = "auto";
    }
}

// Keep your DOMContentLoaded listener as is
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById("imageModal");
    const modalImg = document.getElementById("modalImage");

    // prevent image click from closing modal
    if (modalImg) {
        modalImg.addEventListener('click', (event) => {
            event.stopPropagation();
        });
    }

    // clicking background closes modal
    if (modal) {
        modal.addEventListener('click', () => {
            closeModal();
        });
    }
});
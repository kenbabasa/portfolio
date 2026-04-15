/**
 * Opens the modal and sets the image source
 * @param {string} imgSrc - The filename of the certificate image
 */
function openModal(imgSrc) {
    const modal = document.getElementById("certModal");
    const modalImg = document.getElementById("fullCertImage");
    
    if (modal && modalImg) {
        modal.style.display = "flex";
        // encodeURI handles spaces like the one in 'ITS cert.jpg'
        modalImg.src = encodeURI(imgSrc); 
        document.body.style.overflow = "hidden";
    }
}

function closeModal() {
    const modal = document.getElementById("certModal");
    if (modal) {
        modal.style.display = "none";
        document.body.style.overflow = "auto";
    }
}

// Keep your DOMContentLoaded listener as is
document.addEventListener('DOMContentLoaded', () => {
    const modalImg = document.getElementById("fullCertImage");
    if (modalImg) {
        modalImg.onclick = function(event) {
            event.stopPropagation();
        };
    }
});
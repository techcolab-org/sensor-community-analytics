(function () {
    window.addEventListener("load", function () {

        const isEditPage = window.location.pathname.endsWith("/change/");

        if (!isEditPage) {
            document.querySelector(".field-location").style.display = "none";
        }
    });
})();

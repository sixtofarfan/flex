   
var btn = $('#back-to-top-1');
    $(window).scroll(function() {
        if ($(window).scrollTop() > 700) {
            btn.addClass('show-1');
            console.log("-----method called");
        } else {
            btn.removeClass('show-1');
        }
    });

    btn.on('click', function(e) {
        e.preventDefault();
        $('html, body').animate({scrollTop:0}, '300');
    });
    

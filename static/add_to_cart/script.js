$(document).ready(function() {
    $(".add-to-cart").click(function(event) {
        event.preventDefault(); // Prevent the default link behavior
        var auctionID = $(this).data("auction-id");
        var addToCartURL = $(this).data("add-to-cart-url");
        console.log('CSRF Token:', $('input[name=csrfmiddlewaretoken]').val());

        // Make an AJAX POST request to your Django view
        $.ajax({
            type: "POST",
            url: addToCartURL.replace('0', auctionID), // Replace '0' in the URL with the actual auction ID
            data: {
                'auction_id': auctionID,
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
            },
            dataType: "json",
            success: function(data) {
                // Update the "Add to Cart" icon with the updated quantity
                $("#cart-icon").text(data.total_quantity);
            },
            error: function(xhr, textStatus, errorThrown) {
                console.error(xhr, textStatus, errorThrown);
            }
        });
    });
});

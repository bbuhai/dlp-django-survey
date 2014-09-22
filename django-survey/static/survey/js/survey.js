(function($){
    $(document).ready(function(){
        var alternative_path = $('#alternative'),
            url = alternative_path.attr('data-url'),
            loader = $('#loader');
        console.log('score='+alternative_path.attr('data-score'));

        var compute = function() {
            $.ajax({
                url: url,
                method: 'GET',
                success: function(xhr) {
                    alternative_path.html(xhr);
                },
                error: function(err) {
                    console.log(err);
                }
            })
        };

        setTimeout(compute, 1)
        
    });
}(jQuery))
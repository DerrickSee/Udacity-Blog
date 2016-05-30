$(function() {
  $('a[data-delete]').click(function(){
    var elem = $(this);
    swal({
      title: "Are you sure?",
      text: "Your will not be able to recover this post!",
      type: "warning",
      showCancelButton: true,
      closeOnConfirm: false,
      showLoaderOnConfirm: true
    }, function () {
      $.ajax({
        'type': 'DELETE',
        'url': elem.attr('data-delete')
      }).done(function(obj){
        swal({
          title: "Deleted!",
          text: "Your post has been deleted.",
          type: "success",
        }, function(){
          window.location.href = obj.success_url;
        });
      }).fail(function() {
        swal("Opps!", "Something went wrong. Try again!", "danger");
      })
    });
  })

});

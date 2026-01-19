var faceUtile ={
      width:500,//图片宽度
      height:500,//图片高度
      isOpen:false ,//是否开启摄像头
      promise:null,
      openVideo: function (id) {
        var mythis = this;
        // 先尝试关闭清理
        this.closeVideo();
        
        // 使用 nextTick 思想，虽然这里是原生JS，但用 setTimeout 0 模拟让出主线程，等待DOM更新
        setTimeout(function() {
            // 再次清理，防止残留
            $("video").each(function() {
                if (this.srcObject) {
                    try {
                        this.srcObject.getTracks().forEach(track => track.stop());
                    } catch(e) {}
                }
                $(this).remove();
            });
            $("#myCavans").remove();
            $("#"+id).empty();
            
            let vedioComp = "<video id='myVideo' width='"+mythis.width+"px' height='"+mythis.height+"px' autoplay='autoplay' style='margin-top: 0px; object-fit: fill;'></video>" +
                "<canvas id='myCavans' width='"+mythis.width+"px' height='"+mythis.height+"px' style='display: none'></canvas>";
            $("#"+id).append(vedioComp);
            
            let constraints = {
                video: {width: mythis.width, height: mythis.height},
                audio: false
            };
            
            let video = document.getElementById("myVideo");
            if (!video) return;

            navigator.mediaDevices.getUserMedia(constraints).then(function (MediaStream) {
                mythis.currentStream = MediaStream;
                video.srcObject = MediaStream;
                video.play();
                mythis.isOpen = true;
            }).catch(function (err) {
                console.error("摄像头调用失败", err);
                alert("摄像头调用失败，请检查设备连接或权限");
            });
        }, 200);
    },
    
    closeVideo: function() {
        if (this.currentStream) {
            try {
                this.currentStream.getTracks().forEach(track => track.stop());
            } catch(e) {}
            this.currentStream = null;
        }
        this.isOpen = false;
        try {
            var oldVideo = document.getElementById("myVideo");
            if (oldVideo) {
                oldVideo.srcObject = null;
                if(oldVideo.parentNode) oldVideo.parentNode.removeChild(oldVideo);
            }
            var oldCanvas = document.getElementById("myCavans");
            if(oldCanvas && oldCanvas.parentNode) oldCanvas.parentNode.removeChild(oldCanvas);
        } catch(e) {}
    },

    getDecode:function () {//获取图片decode码
          if(this.isOpen){
              let myVideo = document.getElementById("myVideo");
              let myCavans = document.getElementById("myCavans");
              let ctx = myCavans.getContext('2d');
              ctx.drawImage(myVideo, 0, 0, this.width, this.height);
              var decode = myCavans.toDataURL();
              return decode;
          }else{
              alert("没有开启摄像头");

          }

    }
}



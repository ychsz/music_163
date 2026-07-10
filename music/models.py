from django.db import models
class Comment(models.Model):
    song_id=models.CharField(max_length=50,verbose_name="歌曲ID")
    content=models.TextField(verbose_name="评论内容")
    create_time=models.DateTimeField(auto_now_add=True,verbose_name="评论时间")
    class Meta:
        ordering=['-create_time']
        verbose_name="歌曲评论"
        verbose_name_plural="歌曲评论"
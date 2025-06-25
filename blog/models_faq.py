from django.db import models

class FAQ(models.Model):
    question = models.CharField(max_length=255, verbose_name="Pergunta")
    answer = models.TextField(verbose_name="Resposta")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordem")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question

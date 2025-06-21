from django.db import models
from django.utils.translation import gettext_lazy as _

class PrizeWheelConfig(models.Model):
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Roda da Sorte Ativa?"),
        help_text=_("Controla se a funcionalidade da Roda da Sorte está globalmente ativa.")
    )
    attempts_per_ip_daily = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Tentativas por IP (Diário)"),
        help_text=_("Número máximo de vezes que um único IP pode girar a roda por dia.")
    )
    overall_win_chance = models.DecimalField(
        default=0.5,
        max_digits=5,  # Allows for values like 99.999 or 0.001
        decimal_places=3, # Allows for precision like 0.5% (0.005)
        verbose_name=_("Chance Geral de Ganhar (%)"),
        help_text=_("A probabilidade percentual de um usuário ganhar QUALQUER prémio numa tentativa. Ex: 0.5 para 0.5% de chance (1 em 200). Max 100.")
    )
    # Consider making this a singleton model in the admin or via a package like django-solo
    # For now, we'll assume only one instance of this model will be created/managed.

    def __str__(self):
        return str(_("Configurações da Roda da Sorte"))

    class Meta:
        verbose_name = _("Configuração da Roda da Sorte")
        verbose_name_plural = _("Configurações da Roda da Sorte")

class Prize(models.Model):
    name = models.CharField(
        max_length=255, 
        verbose_name=_("Nome do Prémio")
    )
    description = models.TextField(
        blank=True, 
        verbose_name=_("Descrição")
    )
    probability_weight = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Peso de Probabilidade"),
        help_text=_("Um número maior aumenta a chance relativa de ganhar este prémio. Ex: um prémio com peso 2 tem o dobro da chance de um com peso 1.")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Prémio Ativo?"),
        help_text=_("Se desmarcado, este prémio não poderá ser ganho, mesmo que a roda esteja ativa.")
    )
    quantity = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name=_("Quantidade Disponível"),
        help_text=_("Opcional: Deixe em branco para quantidade ilimitada. Se um número for definido, diminui a cada vez que é ganho.")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Prémio")
        verbose_name_plural = _("Prémios")
        ordering = ['-probability_weight', 'name']

class SpinAttempt(models.Model):
    ip_address = models.GenericIPAddressField(
        verbose_name=_("Endereço IP")
    )
    prize_won = models.ForeignKey(
        Prize, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        verbose_name=_("Prémio Ganho")
    )
    winner_email = models.EmailField(
        max_length=255,
        null=True, 
        blank=True, 
        verbose_name=_("Email do Vencedor"),
        help_text=_("Email coletado se o usuário ganhar um prémio.")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Data/Hora da Tentativa")
    )

    def __str__(self):
        if self.prize_won:
            return f"{self.ip_address} ganhou {self.prize_won.name} em {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
        return f"Tentativa de {self.ip_address} em {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = _("Tentativa na Roda")
        verbose_name_plural = _("Tentativas na Roda")
        ordering = ['-timestamp']


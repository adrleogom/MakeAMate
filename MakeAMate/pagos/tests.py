from django.test import Client, TestCase
from django.contrib.auth.models import User
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from principal.models import Usuario
from pagos.models import Suscripcion
from django.utils.timezone import make_aware, localtime # Import localtime
from django.urls import reverse # reverse already imported, resolve removed as not used
from django.utils import timezone # Import timezone


class PaymentsTest(TestCase):
    
    def setUp(self):
        super().setUp()
        userPepe= User.objects.create_user(username="Pepe", password="asdfg") # Use create_user for password hashing

        userMaria=User.objects.create_user(username="Maria", password="asdfg")
        fecha_premium=datetime(2022,9,22,0,0,0,0) # Consider using timezone.now() for dynamic dates
        aware_fecha_premium=make_aware(fecha_premium)
        
        tfn1 = "+34666777111"
        tfn2 = "+34666777222"
        tfn3 = "+34123123129"
        
        # Ensure Maria is created with sms_validado=True
        self.Maria=Usuario.objects.create(usuario=userMaria, fecha_nacimiento=date(2000,12,30),lugar="Sevilla", fecha_premium=aware_fecha_premium, telefono=tfn1, sms_validado=True)
        # Ensure Pepe is created with sms_validado=True
        self.Pepe= Usuario.objects.create(usuario=userPepe, fecha_nacimiento=date(2000,12,31),lugar="Sevilla", telefono=tfn2, sms_validado=True)
        
        self.plan_premium=Suscripcion.objects.create(id=1,name="Plan Premium", price=4.99, description="!Consigue un boost en tu perfil y además averigua quien ve tu perfil!")
        # self.plan_premium.save() # Not needed, create already saves

        # Add a user for SMS validation tests
        self.user_sms_not_validated_auth = User.objects.create_user(username='pagos_sms_test_user', password='password')
        self.perfil_sms_not_validated = Usuario.objects.create(
            usuario=self.user_sms_not_validated_auth,
            fecha_nacimiento="2000-02-01",
            lugar="TestCityPagos",
            telefono=tfn3, 
            genero='O',
            sms_validado=False # Explicitly False
        )
       

    #Con este test comprobamos que un usuario logeado puede comprar un suscripción
    
    def test_payments(self):
        # c= Client() # client is available as self.client in TestCase
        self.client.login(username='Pepe', password= 'asdfg')
        response=self.client.get(reverse("pagos:pagos")) # Use reverse
        suscripcion=response.context['suscripcion']
        self.assertEqual(suscripcion.name,"Plan Premium")
        self.assertEqual(response.status_code, 200)
    
    #Comprobamos que un usuario deslogegado no puede acceder a la tienda
    
    def test_payments_logout_user(self):
        # c= Client()
        response=self.client.get(reverse("pagos:pagos")) # Use reverse
        self.assertRedirects(response, reverse("login") + "?next=" + reverse("pagos:pagos")) # Check next parameter

    #Comprobamos que se puede comprar la suscripción
    
    def test_paypal(self):
        # c= Client()
        self.client.login(username='Pepe', password= 'asdfg')        
        response=self.client.get(reverse("pagos:paypal", args=[self.plan_premium.id])) # Use reverse
        suscripcion=response.context['suscripcion']
        self.assertEqual(suscripcion.name,"Plan Premium")
        self.assertEqual(response.status_code, 200)
       
        
    
    #Comprobamos que un usuario deslogegado no puede comprar una suscripción

    def test_paypal_user_not_login(self):
        # c= Client()       
        response=self.client.get(reverse("pagos:paypal", args=[self.plan_premium.id])) # Use reverse
        self.assertRedirects(response, reverse("login") + "?next=" + reverse("pagos:paypal", args=[self.plan_premium.id]))

    #Comprobamos que un usuario que ya es premium no puede comprar una suscripción
    
    def test_paypal_user_already_premium(self):
        # c= Client() 
        self.client.login(username='Maria', password= 'asdfg')      
        response=self.client.get(reverse("pagos:paypal", args=[self.plan_premium.id])) # Use reverse
        self.assertRedirects(response, reverse("index")) # Assuming redirect to home page ('/') is named 'index'
   
   #Comprobamos que un usuario deslogegado no puede finalizar una transacción y setear una fecha final de premium
    def test_payment_complete_user_not_login(self):
        # c= Client()
        response=self.client.get(reverse("pagos:complete")) # Use reverse
        # For unauthenticated users, views often redirect to login or raise 403 if @login_required is used.
        # If it's a 404, it implies the URL might not be found or is protected in a way that leads to 404 for anon.
        # Let's assume it redirects to login if @login_required is used.
        # If the view truly returns 404 for not logged in, then self.assertEqual(response.status_code, 404) is correct.
        # Given other tests redirect to login, that's more standard for unauthorized access.
        # However, the original test expects 404. I will keep it, but it's unusual.
        self.assertEqual(response.status_code, 404)

    
    #Comprobamos que un usuario que ya es premium no finalizar una transacción y setear una fecha final de premium
    def test_payment_complete_user_already_premium(self):
        # c= Client()
        self.client.login(username='Maria', password= 'asdfg')
        response=self.client.get(reverse("pagos:complete")) # Use reverse
        # Similar to above, a 404 is unusual for an already premium user.
        # Usually, it would be a redirect to a "you are already premium" page or home.
        # Keeping original assertion of 404.
        self.assertEqual(response.status_code, 404)

    # REPLACED by test_payment_complete_updates_fecha_premium_value
    # def test_payment_complete(self):
    #     c= Client()
    #     c.login(username='Pepe', password= 'asdfg')
    #     response=c.get(reverse("pagos:complete")) # Use reverse
    #     self.Pepe.refresh_from_db() # Refresh to get updated value
    #     self.assertIsNotNone(self.Pepe.fecha_premium) # Changed from assertFalse(..., None)

    def test_payment_complete_updates_fecha_premium_value(self):
       self.client.login(username='Pepe', password='asdfg')
       pepe_profile = Usuario.objects.get(usuario__username='Pepe')
       pepe_profile.fecha_premium = None
       pepe_profile.save()

       response = self.client.get(reverse('pagos:complete')) # Use reverse
       # The original view redirects to /login after completion, which is unusual.
       # Typically, it would redirect to a success page or user profile.
       # Assuming the redirect to 'login' is the intended behavior based on original view logic.
       # If it's supposed to redirect to a different page upon success (e.g., home 'index'), update assertion.
       self.assertRedirects(response, reverse('login')) # Original view redirects to /login.

       pepe_profile.refresh_from_db()
       self.assertIsNotNone(pepe_profile.fecha_premium)
       
       # Using timezone.localtime(timezone.now()) to ensure comparison with aware datetime
       expected_premium_date_aware = timezone.localtime(timezone.now()) + relativedelta(months=1)
       
       # Allow a small delta for comparison due to execution time
       # Ensure pepe_profile.fecha_premium is also aware if it's not already
       pepe_fecha_premium_aware = pepe_profile.fecha_premium
       if timezone.is_naive(pepe_fecha_premium_aware):
           pepe_fecha_premium_aware = make_aware(pepe_fecha_premium_aware, timezone.get_default_timezone())

       self.assertTrue(expected_premium_date_aware - timezone.timedelta(seconds=15) <= pepe_fecha_premium_aware <= expected_premium_date_aware + timezone.timedelta(seconds=15))

    def test_paypal_view_sms_not_validated(self):
       self.client.login(username=self.user_sms_not_validated_auth.username, password='password')
       response = self.client.get(reverse('pagos:paypal', args=[self.plan_premium.id]))
       self.assertRedirects(response, reverse('registerSMS'))

    def test_paypal_view_get_invalid_suscripcion_pk(self):
       self.client.login(username='Pepe', password='asdfg') 
       invalid_pk = 99999 
       response = self.client.get(reverse('pagos:paypal', args=[invalid_pk]))
       self.assertEqual(response.status_code, 404)

    def test_payment_complete_view_sms_not_validated(self):
       self.client.login(username=self.user_sms_not_validated_auth.username, password='password')
       response = self.client.get(reverse('pagos:complete'))
       self.assertRedirects(response, reverse('registerSMS'))

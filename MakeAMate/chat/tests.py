from django.test import TestCase, Client, TransactionTestCase
from chat.models import ChatRoom, Message
from principal.models import Usuario, Mate
from django.contrib.auth.models import User
from channels.testing import WebsocketCommunicator
from chat.consumers import WebsocketConsumer
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.urls import reverse
from cryptography.fernet import Fernet
from chat.forms import CrearGrupo
from chat.consumers import ChatConsumer
# Create your tests here.

class TestChatRoomModel(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password', id=0)
        self.user2 = User.objects.create_user(username='user2', password='password', id=1)
        self.user3 = User.objects.create_user(username='user3', password='password', id=2)
        self.user4 = User.objects.create_user(username='user4', password='password', id=3)
        self.user5 = User.objects.create_user(username='user5', password='password', id=4)
        self.user_sms_not_validated_auth = User.objects.create_user(username='sms_not_validated', password='password', id=5)

        self.perfil1 = Usuario.objects.create(usuario=self.user1, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666661",
                                genero='F', estudios="Informática", sms_validado=True)
        self.perfil2 = Usuario.objects.create(usuario=self.user2, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666662",
                                genero='F', estudios="Informática", sms_validado=True)
        self.perfil3 = Usuario.objects.create(usuario=self.user3, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666663",
                                genero='F', estudios="Informática", sms_validado=True)
        self.perfil4 = Usuario.objects.create(usuario=self.user4, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666664",
                                genero='F', estudios="Informática", sms_validado=True)
        self.perfil5 = Usuario.objects.create(usuario=self.user5, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666665",
                                genero='F', estudios="Informática", sms_validado=True)
        self.perfil_sms_not_validated = Usuario.objects.create(usuario=self.user_sms_not_validated_auth, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666666",
                                genero='M', estudios="Derecho", sms_validado=False)

        Mate.objects.create(userEntrada=self.user1, userSalida=self.user2, mate=True)
        Mate.objects.create(userEntrada=self.user2, userSalida=self.user1, mate=True)
        Mate.objects.create(userEntrada=self.user1, userSalida=self.user3, mate=True)
        Mate.objects.create(userEntrada=self.user3, userSalida=self.user1, mate=True)

        self.chat1 = ChatRoom.objects.create(name="chat1")
        self.chat1.participants.set([self.user1, self.user2])
        self.chat_no_messages = ChatRoom.objects.create(name="chat_no_messages")
        self.chat_no_messages.participants.set([self.user1, self.user4])


    def test_group_method_no_participants(self):
        room = ChatRoom.objects.create(name='Test Room')
        self.assertFalse(room.group())

    def test_group_method_one_participant(self):
        room = ChatRoom.objects.create(name='Test Room')
        room.participants.add(self.user1)
        self.assertFalse(room.group())

    def test_group_method_two_participants(self):
        room = ChatRoom.objects.create(name='Test Room')
        room.participants.add(self.user1, self.user2)
        self.assertFalse(room.group())

    def test_group_method_three_participants(self):
        room = ChatRoom.objects.create(name='Test Room')
        room.participants.add(self.user1, self.user2, self.user3)
        self.assertTrue(room.group())

    def test_public_key_generation(self):
        room = ChatRoom.objects.create(name='Test Room')
        self.assertIsNotNone(room.public_key)
        try:
            Fernet(room.public_key.encode())
        except Exception:
            self.fail("Public key is not a valid Fernet key")

    def test_last_message_default(self):
        room = ChatRoom.objects.create(name='Test Room')
        self.assertEqual(room.last_message, "No se ha enviado ningún mensaje")


class ChatTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(id=0, username="us1", password='123')
        self.user2 = User.objects.create_user(id=1, username="us2", password='123')
        self.user3 = User.objects.create_user(id=2, username="us3", password='123')
        self.user4 = User.objects.create_user(id=3, username="us4", password='123')
        self.user5 = User.objects.create_user(id=4, username="us5", password='123')
        self.user_sms_not_validated_auth = User.objects.create_user(id=5, username="sms_not_validated", password='123')

        self.perfil1 = Usuario.objects.create(usuario=self.user1, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666661",
                                genero='F', estudios="Informática", sms_validado=True)
        self.perfil2 = Usuario.objects.create(usuario=self.user2, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666662",
                                genero='F', estudios="Informática", sms_validado=True)
        self.perfil3 = Usuario.objects.create(usuario=self.user3, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666663",
                                genero='F', estudios="Informática", sms_validado=True)
        self.perfil4 = Usuario.objects.create(usuario=self.user4, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666664",
                                genero='F', estudios="Informática", sms_validado=True)
        self.perfil5 = Usuario.objects.create(usuario=self.user5, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666665",
                                genero='F', estudios="Informática", sms_validado=True)
        self.perfil_sms_not_validated = Usuario.objects.create(usuario=self.user_sms_not_validated_auth, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666666",
                                genero='M', estudios="Derecho", sms_validado=False)

        Mate.objects.create(userEntrada=self.user1, userSalida=self.user2, mate=True)
        Mate.objects.create(userEntrada=self.user2, userSalida=self.user1, mate=True)
        Mate.objects.create(userEntrada=self.user1, userSalida=self.user3, mate=True)
        Mate.objects.create(userEntrada=self.user3, userSalida=self.user1, mate=True)

        self.chat1 = ChatRoom.objects.create(name="5") # Corresponds to old chat1 name
        self.chat1.participants.set([self.user1, self.user2])
        self.chat_no_messages = ChatRoom.objects.create(name="chat_no_msg")
        self.chat_no_messages.participants.set([self.user1, self.user4])


    def test_chat_user1_index(self):
        c = Client()
        c.login(username='us1', password='123')
        response = c.get(reverse('chat:index'))

        self.assertEqual(len(response.context['users']), 2)
        self.assertEqual(len(response.context['chats']), 2) # chat1 and chat_no_messages
        self.assertEqual(len(response.context['nombrechats']), 4) # user2, user3, user4, user5 (all except logged in)

    def test_chat_user5_index(self): # User with no mates, no chats
        c = Client()
        c.login(username='us5', password='123')
        response = c.get(reverse('chat:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['users']), 0)
        self.assertEqual(len(response.context['chats']), 0)


    def test_chat_user1_chatroom(self):
        c = Client()
        c.login(username='us1', password='123')
        response = c.get(reverse('chat:room', args=[self.chat1.name]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['room_name'], self.chat1.name)
        self.assertEqual(len(response.context['users']), 2)
        self.assertEqual(len(response.context['chats']), 2)
        self.assertEqual(len(response.context['nombrechats']), 4)


    def test_chat_user5_chatroom_not_participant(self): # User tries to access chat they are not part of
        c = Client()
        c.login(username='us5', password='123')
        with self.assertRaises(PermissionDenied):
            c.get(reverse('chat:room', args=[self.chat1.name]))


class TestChatForms(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='form_user1', password='password', id=6)
        self.user2 = User.objects.create_user(username='form_user2', password='password', id=7)
        self.user3 = User.objects.create_user(username='form_user3', password='password', id=8)
        self.user4 = User.objects.create_user(username='form_user4', password='password', id=9) # For max selection test
        self.user5 = User.objects.create_user(username='form_user5', password='password', id=10)
        self.user6 = User.objects.create_user(username='form_user6', password='password', id=11)
        self.user7 = User.objects.create_user(username='form_user7', password='password', id=12)
        self.user8 = User.objects.create_user(username='form_user8', password='password', id=13)
        self.user9 = User.objects.create_user(username='form_user9', password='password', id=14)
        self.user10 = User.objects.create_user(username='form_user10', password='password', id=15)
        self.user11 = User.objects.create_user(username='form_user11', password='password', id=16)
        # User for the case where a mate is not validated by SMS
        self.user_mate_not_validated = User.objects.create_user(username='mate_not_validated', password='password', id=18)


        # Create profiles for these users to be choosable in the form
        Usuario.objects.create(usuario=self.user1, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666670", sms_validado=True)
        Usuario.objects.create(usuario=self.user2, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666671", sms_validado=True)
        Usuario.objects.create(usuario=self.user3, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666672", sms_validado=True)
        Usuario.objects.create(usuario=self.user4, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666673", sms_validado=True)
        Usuario.objects.create(usuario=self.user5, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666674", sms_validado=True)
        Usuario.objects.create(usuario=self.user6, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666675", sms_validado=True)
        Usuario.objects.create(usuario=self.user7, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666676", sms_validado=True)
        Usuario.objects.create(usuario=self.user8, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666677", sms_validado=True)
        Usuario.objects.create(usuario=self.user9, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666678", sms_validado=True)
        Usuario.objects.create(usuario=self.user10, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666679", sms_validado=True)
        Usuario.objects.create(usuario=self.user11, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666680", sms_validado=True)
        Usuario.objects.create(usuario=self.user_mate_not_validated, fecha_nacimiento="2000-1-1", lugar="Cadiz", telefono="+34666666688", sms_validado=False)



    def test_crear_grupo_form_init_dynamic_choices(self):
        # Simulate a user making a request (self.user1)
        # Assume user1 has mates with user2 (SMS validated) and user_mate_not_validated (SMS not validated)
        Mate.objects.create(userEntrada=self.user1, userSalida=self.user2, mate=True)
        Mate.objects.create(userEntrada=self.user2, userSalida=self.user1, mate=True)
        Mate.objects.create(userEntrada=self.user1, userSalida=self.user_mate_not_validated, mate=True)
        Mate.objects.create(userEntrada=self.user_mate_not_validated, userSalida=self.user1, mate=True)


        form = CrearGrupo(user=self.user1)
        # Choices should only be user2 because user_mate_not_validated has sms_validado=False
        expected_choices = [(self.user2.id, self.user2.username)]
        actual_choices = list(form.fields['Personas'].queryset.values_list('id', 'username'))
        self.assertCountEqual(actual_choices, expected_choices)


    def test_crear_grupo_form_personas_min_selection_fail(self):
        # Need to ensure there are at least 2 valid choices for this test to be meaningful for min selection
        Mate.objects.create(userEntrada=self.user1, userSalida=self.user2, mate=True)
        Mate.objects.create(userEntrada=self.user2, userSalida=self.user1, mate=True)
        Mate.objects.create(userEntrada=self.user1, userSalida=self.user3, mate=True) # Add another valid mate
        Mate.objects.create(userEntrada=self.user3, userSalida=self.user1, mate=True)

        form_data = {'Nombre': 'Test Group', 'Personas': [self.user2.id]} # Only one person selected
        form = CrearGrupo(data=form_data, user=self.user1)
        self.assertFalse(form.is_valid())
        self.assertIn('Personas', form.errors)
        self.assertEqual(form.errors['Personas'][0], "Debe seleccionar al menos 2 usuarios o no más de 10")

    def test_crear_grupo_form_personas_max_selection_fail(self):
        # Create mates for user1 with 11 other users
        users_for_selection = [
            self.user2, self.user3, self.user4, self.user5, self.user6,
            self.user7, self.user8, self.user9, self.user10, self.user11,
            User.objects.create_user(username='extra_user_form', password='password', id=17) # 11th potential selection
        ]
        Usuario.objects.create(usuario=users_for_selection[-1], fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666690", sms_validado=True)

        for u_mate in users_for_selection:
            Mate.objects.create(userEntrada=self.user1, userSalida=u_mate, mate=True)
            Mate.objects.create(userEntrada=u_mate, userSalida=self.user1, mate=True)

        selected_ids = [u.id for u in users_for_selection]
        form_data = {'Nombre': 'Too Large Group', 'Personas': selected_ids}
        form = CrearGrupo(data=form_data, user=self.user1)
        self.assertFalse(form.is_valid())
        self.assertIn('Personas', form.errors)
        self.assertEqual(form.errors['Personas'][0], "Debe seleccionar al menos 2 usuarios o no más de 10")

    def test_crear_grupo_form_personas_valid_selection(self):
        Mate.objects.create(userEntrada=self.user1, userSalida=self.user2, mate=True)
        Mate.objects.create(userEntrada=self.user2, userSalida=self.user1, mate=True)
        Mate.objects.create(userEntrada=self.user1, userSalida=self.user3, mate=True)
        Mate.objects.create(userEntrada=self.user3, userSalida=self.user1, mate=True)
        form_data = {'Nombre': 'Valid Group', 'Personas': [self.user2.id, self.user3.id]}
        form = CrearGrupo(data=form_data, user=self.user1)
        self.assertTrue(form.is_valid())

    def test_crear_grupo_form_nombre_too_long(self):
        Mate.objects.create(userEntrada=self.user1, userSalida=self.user2, mate=True) # Ensure form can be valid otherwise
        Mate.objects.create(userEntrada=self.user2, userSalida=self.user1, mate=True)
        Mate.objects.create(userEntrada=self.user1, userSalida=self.user3, mate=True)
        Mate.objects.create(userEntrada=self.user3, userSalida=self.user1, mate=True)
        long_name = 'a' * 41
        form_data = {'Nombre': long_name, 'Personas': [self.user2.id, self.user3.id]}
        form = CrearGrupo(data=form_data, user=self.user1)
        self.assertFalse(form.is_valid())
        self.assertIn('Nombre', form.errors)
        self.assertEqual(form.errors['Nombre'][0], "El nombre no puede tener más de 40 caracteres")

    def test_crear_grupo_form_nombre_valid(self):
        Mate.objects.create(userEntrada=self.user1, userSalida=self.user2, mate=True) # Ensure form can be valid otherwise
        Mate.objects.create(userEntrada=self.user2, userSalida=self.user1, mate=True)
        Mate.objects.create(userEntrada=self.user1, userSalida=self.user3, mate=True)
        Mate.objects.create(userEntrada=self.user3, userSalida=self.user1, mate=True)
        form_data = {'Nombre': 'Good Name', 'Personas': [self.user2.id, self.user3.id]}
        form = CrearGrupo(data=form_data, user=self.user1)
        self.assertTrue(form.is_valid())


class TestChatConsumer(TransactionTestCase):
    async def asyncSetUp(self):
        self.user_consumer1 = await User.objects.acreate(username='consumer1', password='password', id=20)
        self.user_consumer2 = await User.objects.acreate(username='consumer2', password='password', id=21)
        self.user_not_participant = await User.objects.acreate(username='consumer_non_participant', password='password', id=22)

        await Usuario.objects.acreate(usuario=self.user_consumer1, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666681", sms_validado=True)
        await Usuario.objects.acreate(usuario=self.user_consumer2, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666682", sms_validado=True)
        await Usuario.objects.acreate(usuario=self.user_not_participant, fecha_nacimiento="2000-1-1", lugar="Sevilla", telefono="+34666666683", sms_validado=True)


        self.room = await ChatRoom.objects.acreate(name='testroomconsumer')
        await self.room.participants.aadd(self.user_consumer1, self.user_consumer2)

        self.room_no_messages = await ChatRoom.objects.acreate(name='testroom_no_msg_consumer')
        await self.room_no_messages.participants.aadd(self.user_consumer1)

    async def test_consumer_connect_not_participant(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.name}/")
        communicator.scope['user'] = self.user_not_participant
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)

    async def test_consumer_connect_non_existent_room(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/nonexistentroomconsumer/")
        communicator.scope['user'] = self.user_consumer1
        # This test assumes that URL routing or middleware handles non-existent rooms before the consumer's connect() is called,
        # or that the consumer's connect() method correctly raises an error like ChatRoom.DoesNotExist if it tries to fetch the room.
        # If using Django Channels routing, the connection might simply be rejected if no route matches.
        # If the consumer's connect method is reached and tries to fetch a non-existent room:
        with self.assertRaises(ChatRoom.DoesNotExist): # Or a more specific error if the consumer handles it differently
             await communicator.connect()
        # If the connection is just closed without an exception bubbling up to here:
        # connected, _ = await communicator.connect()
        # self.assertFalse(connected)


    async def test_consumer_connect_updates_last_connection(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.name}/")
        communicator.scope['user'] = self.user_consumer1
        initial_time = timezone.now() - timezone.timedelta(days=1)
        profile = await Usuario.objects.aget(usuario=self.user_consumer1)
        profile.last_connection = initial_time
        await profile.asave()

        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

        updated_profile = await Usuario.objects.aget(usuario=self.user_consumer1)
        self.assertGreater(updated_profile.last_connection, initial_time)


    async def test_consumer_disconnect_updates_last_connection(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.name}/")
        communicator.scope['user'] = self.user_consumer1
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        # Ensure last_connection is not None and slightly in the past before disconnect
        profile = await Usuario.objects.aget(usuario=self.user_consumer1)
        profile.last_connection = timezone.now() - timezone.timedelta(seconds=10)
        await profile.asave()
        time_before_disconnect = profile.last_connection


        await communicator.disconnect()

        profile = await Usuario.objects.aget(usuario=self.user_consumer1)
        self.assertIsNotNone(profile.last_connection)
        self.assertGreater(profile.last_connection, time_before_disconnect)


    async def test_consumer_receive_invalid_json(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.name}/")
        communicator.scope['user'] = self.user_consumer1
        await communicator.connect()
        await communicator.send_to(text_data="this is not json")
        # Expect no message back, or an error message if consumer is set up to send one
        # For this test, we just check it doesn't crash and no standard message is processed
        received = await communicator.receive_nothing(timeout=0.2)
        self.assertTrue(received)
        await communicator.disconnect()

    async def test_consumer_receive_empty_message_string(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.name}/")
        communicator.scope['user'] = self.user_consumer1
        await communicator.connect()
        await communicator.send_json_to({'message': ''})
        self.assertTrue(await communicator.receive_nothing(timeout=0.2))
        message_count = await Message.objects.filter(room=self.room).acount()
        self.assertEqual(message_count, 0)
        await communicator.disconnect()


    async def test_consumer_store_message_updates_room_last_message(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.name}/")
        communicator.scope['user'] = self.user_consumer1
        await communicator.connect()

        test_message = "Hello, this is a test message!"
        await communicator.send_json_to({'message': test_message})
        response = await communicator.receive_json_from(timeout=1)
        self.assertEqual(response['message'], test_message) # Check broadcasted message

        await self.room.arefresh_from_db()
        key = await ChatRoom.objects.values_list('public_key', flat=True).aget(name=self.room.name)
        fernet = Fernet(key.encode())
        decrypted_last_message = fernet.decrypt(self.room.last_message.encode()).decode()
        self.assertEqual(decrypted_last_message, test_message)

        await communicator.disconnect()


    async def test_consumer_store_message_encryption(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.name}/")
        communicator.scope['user'] = self.user_consumer1
        await communicator.connect()

        plain_message = "This is a secret message."
        await communicator.send_json_to({'message': plain_message})
        await communicator.receive_json_from(timeout=1) # Consume broadcast

        db_message = await Message.objects.aget(room=self.room, author=self.user_consumer1)
        self.assertNotEqual(db_message.content, plain_message)

        key = await ChatRoom.objects.values_list('public_key', flat=True).aget(name=self.room.name)
        fernet = Fernet(key.encode())
        decrypted_content = fernet.decrypt(db_message.content.encode()).decode()
        self.assertEqual(decrypted_content, plain_message)
        await communicator.disconnect()

    async def test_consumer_get_all_messages_no_messages(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room_no_messages.name}/")
        communicator.scope['user'] = self.user_consumer1
        await communicator.connect()
        await communicator.send_json_to({'command': 'get_all_messages'})
        # Check for a specific response indicating no messages, or that receive_nothing is true.
        # If the consumer sends `{'type': 'no_messages'}` or `{'messages': []}`:
        # response = await communicator.receive_json_from(timeout=0.5)
        # self.assertIn(response.get('type'), ['no_messages', 'chat_message_history']) # if chat_message_history, messages list should be empty
        # if response.get('type') == 'chat_message_history':
        #     self.assertEqual(len(response.get('messages', [])), 0)
        # For now, assuming it might send nothing if no messages, or an empty history list
        response = await communicator.receive_json_from(timeout=0.5) # Expecting a response now
        self.assertEqual(response['type'], 'chat_message_history')
        self.assertEqual(len(response['messages']),0)

        await communicator.disconnect()


    async def test_consumer_get_all_messages_order_and_decryption(self):
        key_bytes = self.room.public_key.encode()
        fernet = Fernet(key_bytes)
        msg1_content = "Oldest message"
        msg2_content = "Newer message"
        msg3_content = "Newest message"

        # Create messages with slight time differences
        time_now = timezone.now()
        await Message.objects.acreate(
            room=self.room, author=self.user_consumer1,
            content=fernet.encrypt(msg1_content.encode()).decode(),
            timestamp=time_now - timezone.timedelta(minutes=2)
        )
        await Message.objects.acreate(
            room=self.room, author=self.user_consumer2,
            content=fernet.encrypt(msg2_content.encode()).decode(),
            timestamp=time_now - timezone.timedelta(minutes=1)
        )
        await Message.objects.acreate(
            room=self.room, author=self.user_consumer1,
            content=fernet.encrypt(msg3_content.encode()).decode(),
            timestamp=time_now
        )
        # No need to call self.room.asave() as last_message is updated by signals/consumer logic

        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.name}/")
        communicator.scope['user'] = self.user_consumer1
        await communicator.connect()

        await communicator.send_json_to({'command': 'get_all_messages'})

        # Expecting a single message of type 'chat_message_history' containing all messages
        response = await communicator.receive_json_from(timeout=2) # Increased timeout
        self.assertEqual(response['type'], 'chat_message_history')
        
        received_messages_payload = response['messages']
        self.assertEqual(len(received_messages_payload), 3)

        # Messages should be decrypted and in correct order (oldest to newest)
        self.assertEqual(received_messages_payload[0]['message'], msg1_content)
        self.assertEqual(received_messages_payload[0]['author'], self.user_consumer1.username)
        self.assertEqual(received_messages_payload[1]['message'], msg2_content)
        self.assertEqual(received_messages_payload[1]['author'], self.user_consumer2.username)
        self.assertEqual(received_messages_payload[2]['message'], msg3_content)
        self.assertEqual(received_messages_payload[2]['author'], self.user_consumer1.username)

        await communicator.disconnect()

    def test_chat_user_non_existent_chatroom(self): # User tries to access a chat that does not exist
        c = Client()
        c.login(username='us1', password='123')
        with self.assertRaises(PermissionDenied): # Or Http404 depending on implementation
            c.get(reverse('chat:room', args=['nonexistentroom']))


    def test_anon_user_index(self):
        c = Client()
        response = c.get(reverse('chat:index'))
        self.assertEqual(response.status_code, 302) # Redirects to login
        self.assertIn(reverse('login'), response.url)


    def test_anon_user_chatroom(self):
        c = Client()
        response = c.get(reverse('chat:room', args=[self.chat1.name]))
        self.assertEqual(response.status_code, 302) # Redirects to login
        self.assertIn(reverse('login'), response.url)


    def test_form_group_positive(self):
        c = Client()
        c.login(username='us1', password='123')
        initial_chat_count = ChatRoom.objects.count()
        response = c.post(reverse('chat:index'), data={'Nombre': 'GrupoTest', 'Personas': [self.user2.id, self.user3.id]})
        self.assertEqual(response.status_code, 302) # Redirects after successful post
        self.assertEqual(ChatRoom.objects.count(), initial_chat_count + 1)
        new_chat = ChatRoom.objects.latest('id')
        self.assertEqual(new_chat.name, 'GrupoTest')
        self.assertIn(self.user1, new_chat.participants.all())
        self.assertIn(self.user2, new_chat.participants.all())
        self.assertIn(self.user3, new_chat.participants.all())

    def test_index_view_sms_not_validated(self):
        c = Client()
        c.login(username='sms_not_validated', password='123')
        response = c.get(reverse('chat:index'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('registerSMS'))

    def test_index_view_no_chats_no_mates_scenario(self):
        c = Client()
        # user5 has no mates and no chats by default from setUp
        c.login(username='us5', password='123')
        response = c.get(reverse('chat:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['chats']), 0)
        self.assertEqual(len(response.context['users']), 0) # users here means potential chat partners from mates

    def test_index_view_chat_with_no_messages(self):
        c = Client()
        c.login(username='us1', password='123')
        response = c.get(reverse('chat:index'))
        self.assertEqual(response.status_code, 200)
        # Find the chat_no_messages in the context
        chat_in_context = None
        for chat_obj in response.context['chats']:
            if chat_obj.name == self.chat_no_messages.name:
                chat_in_context = chat_obj
                break
        self.assertIsNotNone(chat_in_context)
        self.assertEqual(chat_in_context.last_message, "No se ha enviado ningún mensaje")


    def test_room_view_sms_not_validated(self):
        c = Client()
        c.login(username='sms_not_validated', password='123')
        response = c.get(reverse('chat:room', args=[self.chat1.name])) # Any valid room name
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('registerSMS'))

    def test_room_view_not_participant(self):
        c = Client()
        c.login(username='us3', password='123') # user3 is not in self.chat1
        with self.assertRaises(PermissionDenied):
            c.get(reverse('chat:room', args=[self.chat1.name]))
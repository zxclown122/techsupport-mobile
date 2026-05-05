import kivy
kivy.require('2.2.0')
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, ListProperty, StringProperty
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.lang import Builder
import api_client
import os

Window.clearcolor = (0.2, 0.2, 0.2, 1)

kv_dir = 'kv'
kv_files = ['login.kv', 'main.kv', 'create_ticket.kv', 'my_tickets.kv',
            'ticket_detail.kv', 'reports.kv', 'all_tickets.kv', 'diagnostics.kv']
for kv_file in kv_files:
    kv_path = os.path.join(kv_dir, kv_file)
    if os.path.exists(kv_path):
        Builder.load_file(kv_path)

class LoginScreen(Screen):
    def do_login(self):
        login_input = self.ids.get('login_input')
        password_input = self.ids.get('password_input')
        if not login_input or not password_input:
            self.show_error("Ошибка интерфейса")
            return
        login = login_input.text.strip()
        pwd = password_input.text
        if not login or not pwd:
            self.show_error("Заполните все поля")
            return
        success, data = api_client.login(login, pwd)
        if success:
            user = data.get('user', {})
            role = user.get('role', '')
            allowed_roles = ['USER', 'MANAGER']
            if role not in allowed_roles:
                self.show_error("Доступ запрещён. Мобильное приложение только для сотрудников и руководителей IT-службы.")
                api_client.logout()
                return
            self.manager.current = 'main'
        else:
            self.show_error(str(data))

    def show_error(self, msg):
        popup = Popup(title='Ошибка', content=Button(text=msg), size_hint=(0.8, 0.3))
        popup.open()

class MainScreen(Screen):
    def on_enter(self):
        user = api_client.get_current_user()
        if user:
            self.ids.user_label.text = f"{user['fullName']} ({user['role']})"
            self.show_buttons_by_role(user['role'])
        self._start_sync()

    def _start_sync(self):
        self.sync_event = Clock.schedule_interval(self._check_updates, 10)

    def _check_updates(self, dt):
        user = api_client.get_current_user()
        if user and user['role'] == 'MANAGER':
            if hasattr(self, 'page_all') and self.page_all:
                self.page_all.refresh()
        elif hasattr(self, 'page_my') and self.page_my:
            self.page_my.refresh()

    def on_leave(self):
        if hasattr(self, 'sync_event') and self.sync_event:
            self.sync_event.cancel()

    def show_buttons_by_role(self, role):
        container = self.ids.buttons_container
        container.clear_widgets()
        if role == 'USER':
            btn_create = Button(text='Создать заявку', background_color=(0.8,0.8,0.8,1),
                               color=(0,0,0,1), size_hint_y=None, height=50)
            btn_create.bind(on_release=lambda x: self.go_create_ticket())
            container.add_widget(btn_create)
            btn_my_tickets = Button(text='Мои заявки', background_color=(0.8,0.8,0.8,1),
                                   color=(0,0,0,1), size_hint_y=None, height=50)
            btn_my_tickets.bind(on_release=lambda x: self.go_my_tickets())
            container.add_widget(btn_my_tickets)
        elif role == 'MANAGER':
            btn_all_tickets = Button(text='Все заявки', background_color=(0.8,0.8,0.8,1),
                                    color=(0,0,0,1), size_hint_y=None, height=50)
            btn_all_tickets.bind(on_release=lambda x: self.go_all_tickets())
            container.add_widget(btn_all_tickets)
            btn_export_excel = Button(text='Выгрузить отчёты Excel', background_color=(0.8,0.8,0.8,1),
                                      color=(0,0,0,1), size_hint_y=None, height=50)
            btn_export_excel.bind(on_release=lambda x: self.export_reports_excel())
            container.add_widget(btn_export_excel)
        container.height = container.minimum_height

    def show_error(self, msg):
        popup = Popup(title='Ошибка', content=Button(text=msg), size_hint=(0.8, 0.3))
        popup.open()

    def show_success(self, msg):
        popup = Popup(title='Успех', content=Button(text=msg), size_hint=(0.8, 0.3))
        popup.open()

    def export_reports_excel(self):
        token = api_client.get_token()
        if not token:
            self.show_error("Не авторизован")
            return
        import requests
        from datetime import datetime
        url = f"{api_client.API_BASE}/reports/export/excel"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                filename = f"tickets_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                with open(filename, 'wb') as f:
                    f.write(r.content)
                self.show_success(f"Отчёт сохранён: {filename}")
            else:
                self.show_error(f"Ошибка: {r.text}")
        except Exception as e:
            self.show_error(str(e))

    def show_menu(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        info_label = Label(text=f"Роль: {api_client.get_user_role()}", color=(0,0,0,1), size_hint_y=None, height=50)
        btn_logout = Button(text='Выход', size_hint_y=None, height=50, background_color=(0.8,0.8,0.8,1), color=(0,0,0,1))
        btn_logout.bind(on_release=lambda x: self.logout())
        btn_close = Button(text='Закрыть', size_hint_y=None, height=50, background_color=(0.8,0.8,0.8,1), color=(0,0,0,1))
        content.add_widget(info_label)
        content.add_widget(btn_logout)
        content.add_widget(btn_close)
        popup = Popup(title='Меню', content=content, size_hint=(0.7, 0.4))
        btn_close.bind(on_release=popup.dismiss)
        popup.open()

    def logout(self):
        api_client.logout()
        self.manager.current = 'login'

    def go_create_ticket(self):
        self.manager.current = 'create_ticket'

    def go_my_tickets(self):
        self.manager.current = 'my_tickets'

    def go_all_tickets(self):
        self.manager.current = 'all_tickets'

class CreateTicketScreen(Screen):
    def go_back(self):
        self.manager.current = 'main'

    def submit_ticket(self):
        title = self.ids.title_input.text
        desc = self.ids.desc_input.text
        type_ = self.ids.type_spinner.text
        if not title or not desc:
            self.show_error("Заполните заголовок и описание")
            return
        type_map = {
            'Инцидент': 'INCIDENT',
            'Запрос': 'REQUEST',
            'Аппаратная проблема': 'HARDWARE',
            'Проблема с ПО': 'SOFTWARE',
            'Сеть': 'NETWORK'
        }
        type_en = type_map.get(type_, 'INCIDENT')
        priority = 'MEDIUM'
        success, result = api_client.create_ticket(title, desc, priority, type_en)
        if success:
            self.manager.current = 'main'
        else:
            self.show_error(str(result))

    def show_error(self, msg):
        popup = Popup(title='Ошибка', content=Button(text=msg), size_hint=(0.8, 0.3))
        popup.open()

class MyTicketsScreen(Screen):
    update_event = None

    def on_enter(self):
        self.load_tickets()
        self.update_event = Clock.schedule_interval(self.refresh_tickets, 10)

    def refresh_tickets(self, dt):
        self.load_tickets()

    def on_leave(self):
        if self.update_event:
            self.update_event.cancel()

    def load_tickets(self):
        container = self.ids.tickets_container
        container.clear_widgets()
        data = api_client.get_tickets(my_only=True)
        if data and data['items']:
            for ticket in data['items']:
                row = BoxLayout(size_hint_y=None, height=50)
                btn = Button(text=ticket['title'], background_color=(0.9,0.9,0.9,1), color=(0,0,0,1))
                btn.bind(on_release=lambda x, tid=ticket['id']: self.open_ticket(tid))
                status_text = {
                    'CREATED': 'Создана', 'ACTIVE': 'В работе', 'COMPLETED': 'Завершена', 'CANCELLED': 'Отменена',
                    'NEW': 'Новая', 'IN_PROGRESS': 'В работе', 'DIAGNOSTICS': 'Диагностика', 'WAITING': 'Ожидание',
                    'ASSIGNED': 'Назначена', 'CLOSED': 'Закрыта'
                }.get(ticket['status'], ticket['status'])
                status_label = Label(text=status_text, color=(0,0,0,1))
                date_label = Label(text=ticket['created_at'][:10], color=(0,0,0,1))
                row.add_widget(btn)
                row.add_widget(status_label)
                row.add_widget(date_label)
                container.add_widget(row)
            container.height = len(data['items']) * 50
        else:
            container.height = 50
            container.add_widget(Label(text="Нет заявок", color=(0.5,0.5,0.5,1)))

    def open_ticket(self, ticket_id):
        detail_screen = self.manager.get_screen('ticket_detail')
        detail_screen.ticket_id = ticket_id
        self.manager.current = 'ticket_detail'

class AllTicketsScreen(Screen):
    update_event = None

    def on_enter(self):
        self.load_tickets()
        self.update_event = Clock.schedule_interval(self.refresh_tickets, 10)

    def refresh_tickets(self, dt):
        self.load_tickets()

    def on_leave(self):
        if self.update_event:
            self.update_event.cancel()

    def load_tickets(self):
        container = self.ids.tickets_container
        container.clear_widgets()
        data = api_client.get_tickets(my_only=False)
        if data and data['items']:
            for ticket in data['items']:
                row = BoxLayout(size_hint_y=None, height=50)
                id_label = Label(text=str(ticket['id']), color=(0,0,0,1), size_hint_x=0.15)
                title_btn = Button(text=ticket['title'][:25], background_color=(0.9,0.9,0.9,1), color=(0,0,0,1), size_hint_x=0.45)
                title_btn.bind(on_release=lambda x, tid=ticket['id']: self.open_ticket(tid))
                status_text = {
                    'CREATED': 'Создана', 'ACTIVE': 'В работе', 'COMPLETED': 'Завершена', 'CANCELLED': 'Отменена',
                    'NEW': 'Новая', 'IN_PROGRESS': 'В работе', 'DIAGNOSTICS': 'Диагностика', 'WAITING': 'Ожидание',
                    'ASSIGNED': 'Назначена', 'CLOSED': 'Закрыта'
                }.get(ticket['status'], ticket['status'])
                status_label = Label(text=status_text, color=(0,0,0,1), size_hint_x=0.2)
                author_label = Label(text=ticket['created_by']['fullName'][:12], color=(0,0,0,1), size_hint_x=0.2)
                row.add_widget(id_label)
                row.add_widget(title_btn)
                row.add_widget(status_label)
                row.add_widget(author_label)
                container.add_widget(row)
            container.height = len(data['items']) * 50
        else:
            container.height = 50
            container.add_widget(Label(text="Нет заявок", color=(0.5,0.5,0.5,1)))

    def open_ticket(self, ticket_id):
        detail_screen = self.manager.get_screen('ticket_detail')
        detail_screen.ticket_id = ticket_id
        self.manager.current = 'ticket_detail'

class TicketDetailScreen(Screen):
    ticket_id = None
    update_event = None

    def on_enter(self):
        self.load_messages()
        self.update_event = Clock.schedule_interval(self.refresh_messages, 5)

    def refresh_messages(self, dt):
        self.load_messages()

    def load_messages(self):
        if not self.ticket_id:
            return
        data = api_client.get_ticket_details(self.ticket_id)
        if data:
            self.ids.title_label.text = data['title']
            status_text = {
                'CREATED': 'Создана', 'ACTIVE': 'В работе', 'COMPLETED': 'Завершена', 'CANCELLED': 'Отменена',
                'NEW': 'Новая', 'IN_PROGRESS': 'В работе', 'DIAGNOSTICS': 'Диагностика', 'WAITING': 'Ожидание',
                'ASSIGNED': 'Назначена', 'CLOSED': 'Закрыта'
            }.get(data['status'], data['status'])
            self.ids.status_label.text = status_text
            container = self.ids.messages_container
            container.clear_widgets()
            for msg in data.get('comments', []):
                msg_box = BoxLayout(orientation='vertical', size_hint_y=None, height=60)
                author_text = Label(text=f"{msg['author']}: {msg['text']}", color=(0,0,0,1), size_hint_y=None, height=40, text_size=(self.width-30, None))
                date_text = Label(text=msg['created_at'][:16], color=(0.4,0.4,0.4,1), font_size='10sp', size_hint_y=None, height=20)
                msg_box.add_widget(author_text)
                msg_box.add_widget(date_text)
                container.add_widget(msg_box)
            container.height = len(data.get('comments', [])) * 60
        else:
            self.ids.title_label.text = "Ошибка загрузки"

    def send_message(self):
        text = self.ids.message_input.text
        if text.strip():
            api_client.add_comment(self.ticket_id, text)
            self.ids.message_input.text = ''
            self.load_messages()

    def on_leave(self):
        if self.update_event:
            self.update_event.cancel()

class ReportsScreen(Screen):
    def on_enter(self):
        user = api_client.get_current_user()
        container = self.ids.reports_container
        container.clear_widgets()
        if user and user['role'] in ['MANAGER', 'ADMIN']:
            self.ids.info_label.text = 'Доступные отчёты:'
            btn1 = Button(text='Отчёт по заявкам', background_color=(0.8,0.8,0.8,1), color=(0,0,0,1), size_hint_y=None, height=50)
            btn2 = Button(text='Отчёт по SLA', background_color=(0.8,0.8,0.8,1), color=(0,0,0,1), size_hint_y=None, height=50)
            btn3 = Button(text='Отчёт по сотрудникам', background_color=(0.8,0.8,0.8,1), color=(0,0,0,1), size_hint_y=None, height=50)
            container.add_widget(btn1)
            container.add_widget(btn2)
            container.add_widget(btn3)
        else:
            self.ids.info_label.text = 'Ваши заявки (SLA)'
            container.add_widget(Label(text='Статистика в разработке', color=(0.5,0.5,0.5,1), size_hint_y=None, height=50))
        container.height = container.minimum_height

class TechSupportApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(CreateTicketScreen(name='create_ticket'))
        sm.add_widget(MyTicketsScreen(name='my_tickets'))
        sm.add_widget(AllTicketsScreen(name='all_tickets'))
        sm.add_widget(TicketDetailScreen(name='ticket_detail'))
        sm.add_widget(ReportsScreen(name='reports'))
        return sm

if __name__ == '__main__':
    TechSupportApp().run()
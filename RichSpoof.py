# language: python, file: RichSpoof.py
from base_plugin import BasePlugin, HookResult, HookStrategy
from client_utils import get_send_messages_helper, get_messages_controller
from org.telegram.tgnet import TLRPC
from java.util import ArrayList
from org.telegram.messenger import MessageObject, MessagesController, MessagesStorage, UserConfig, NotificationCenter
from android.util import Toast
import time

# ================= МЕТАДАННЫЕ ПЛАГИНА =================
__id__ = "rich_spoof_pro_max"
__name__ = "Rich Spoof (+888 & Premium)"
__description__ = "Визуальный вход на аккаунты +888, подмена профиля, фейковые звезды и отправка NFT-подарков."
__author__ = "@tgsteve | Onyx"
__version__ = "2.0"
__requirements__ = "ExteraGram 10.2.0+"
# =======================================================

class RichSpoofPlugin(BasePlugin):
    def __init__(self):
        super().__init__()

    def on_plugin_load(self):
        self.add_on_send_message_hook()

    # ================= 1. ПОДМЕНА ПРОФИЛЯ =================
    def set_peer_premium(self, account, user_id, is_self=False):
        """Локальная выдача значка премиума, звезд и подарков"""
        mc = MessagesController.getInstance(account)
        user = mc.getUser(user_id)
        if user:
            user.premium = True
            user.verified = True
            user.stars_balance = 999999  # 999к звезд
            
            # Фейковые подарки в профиле
            user.stars_gifts = ArrayList()
            for name in ["🌹 Роза", "🧸 Мишка", "💎 Алмаз", "👑 Корона", "🚀 Ракета"]:
                gift = TLRPC.TL_userStarGift()
                gift.name = name
                gift.is_hidden = False
                user.stars_gifts.add(gift)

            # Если это твой профиль, меняем имя и номер
            if is_self:
                user.first_name = "Missed"
                user.last_name = "Official"
                user.phone = "+888"
                user.username = "missed_real"

            user.flags |= 2048 
            
            nc = NotificationCenter.getInstance(account)
            nc.postNotificationName(NotificationCenter.userFullInfoDidLoad, user_id, None, None)
            nc.postNotificationName(NotificationCenter.updateInterfaces, 65535)
            return True
        return False

    # ================= 2. СОЗДАНИЕ ПОДАРКА =================
    def create_gift_msg(self, account, peer_id, gift_type, price_cents=500):
        """Создает фейковое сообщение о подарке"""
        if gift_type == "premium":
            action = TLRPC.TL_messageActionGiftPremium()
            action.months = 12
            action.currency = "USD"
            action.amount = price_cents
        else:
            action = TLRPC.TL_messageActionGiftStars()
            action.stars = price_cents
            action.currency = "XTR"
        
        if hasattr(action, 'flags'):
            action.flags |= 3

        msg = TLRPC.TL_messageService()
        msg.action = action
        msg.id = UserConfig.getInstance(account).getNewMessageId()
        UserConfig.getInstance(account).saveConfig(False)
        
        msg.peer_id = TLRPC.TL_peerUser()
        msg.peer_id.user_id = peer_id
        
        msg.from_id = TLRPC.TL_peerUser()
        msg.from_id.user_id = UserConfig.getInstance(account).getClientUserId()
        
        msg.date = int(time.time())
        msg.out = True 
        msg.unread = False
        msg.flags = 256
        
        return msg

    def inject_local_msg(self, account, peer_id, msg_tl):
        """Вставляет сообщение в чат (визуально)"""
        mc = get_messages_controller()
        msg_obj = MessageObject(account, msg_tl, False, True)
        
        current_msgs = mc.dialogMessage.get(peer_id)
        if current_msgs is None:
            current_msgs = ArrayList()
            mc.dialogMessage.put(peer_id, current_msgs)
        current_msgs.add(0, msg_obj)
        
        store_arr = ArrayList()
        store_arr.add(msg_tl)
        MessagesStorage.getInstance(account).putMessages(store_arr, True, True, False, 1, 0, 0)
        
        hist_arr = ArrayList()
        hist_arr.add(msg_obj)
        mc.updateInterfaceWithMessages(peer_id, hist_arr, 0)
        
        NotificationCenter.getInstance(account).postNotificationName(NotificationCenter.dialogsNeedReload)

    # ================= 3. КОМАНДЫ В ЧАТЕ =================
    def on_send_message_hook(self, account, params) -> HookResult:
        msg_text = ""
        if hasattr(params, 'message') and isinstance(params.message, str):
            msg_text = params.message
        elif hasattr(params, 'caption') and isinstance(params.caption, str):
            msg_text = params.caption

        text_lower = msg_text.strip().lower()

        # --- Команда .888 ---
        if text_lower == ".888":
            res = HookResult(strategy=HookStrategy.CANCEL)
            try:
                self.set_peer_premium(account, UserConfig.getInstance(account).getClientUserId(), is_self=True)
                Toast.makeText(self.activity, "Визуальный вход на +888 успешен!", 0).show()
            except Exception as e:
                self.log(f"888 Error: {e}")
            return res

        # --- Команда .gift prem ---
        if text_lower == ".gift prem":
            res = HookResult(strategy=HookStrategy.CANCEL)
            try:
                peer_id = params.peer
                if peer_id > 0:
                    msg = self.create_gift_msg(account, peer_id, "premium", 4999)
                    self.inject_local_msg(account, peer_id, msg)
                    Toast.makeText(self.activity, "Premium отправлен (визуально)!", 0).show()
            except Exception as e:
                self.log(f"Gift Error: {e}")
            return res

        # --- Команда .gift nft ---
        if text_lower == ".gift nft":
            res = HookResult(strategy=HookStrategy.CANCEL)
            try:
                peer_id = params.peer
                if peer_id > 0:
                    msg = self.create_gift_msg(account, peer_id, "nft", 1500)
                    self.inject_local_msg(account, peer_id, msg)
                    Toast.makeText(self.activity, "NFT подарок отправлен (визуально)!", 0).show()
            except Exception as e:
                self.log(f"Gift Error: {e}")
            return res
            
        return HookResult()

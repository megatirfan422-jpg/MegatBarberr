import streamlit as st
import pandas as pd
import os
from datetime import datetime
from urllib.parse import quote

# ===================================================================
# KONFIGURASI APLIKASI
# ===================================================================
st.set_page_config(page_title="Megat Barber", page_icon="💈", layout="wide")

BARBER_PASSWORD = st.secrets.get("BARBER_PASSWORD", "123") 
BARBER_WHATSAPP = "60143324491"

# Nama-nama fail CSV
FILES = {
    "bookings": "bookings.csv",
    "availability": "availability.csv",
    "history": "history.csv",
    "walkin": "walkin.csv"
}

# Definisi lajur untuk setiap fail
COLUMNS = {
    "bookings": ["booking_id", "date", "name", "phone", "service", "slot", "price", "status"],
    "availability": ["date", "time"],
    "history": ["booking_id", "date", "name", "phone", "service", "slot", "price", "status"],
    "walkin": ["queue_id", "name", "status"]
}

# ===================================================================
# FUNGSI-FUNGSI BANTUAN
# ===================================================================
def init_app():
    """Inisialisasi session state dan pastikan semua fail CSV wujud."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    for key, filename in FILES.items():
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            pd.DataFrame(columns=COLUMNS[key]).to_csv(filename, index=False)

def read_csv(file_key):
    """Membaca fail CSV dengan selamat."""
    try:
        df = pd.read_csv(FILES[file_key])
        for col in COLUMNS[file_key]:
            if col not in df.columns: df[col] = None
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=COLUMNS[file_key])

def generate_unique_booking_id():
    """Menjana ID unik untuk tempahan."""
    df_bookings = read_csv("bookings"); df_history = read_csv("history")
    all_ids = set(pd.concat([df_bookings['booking_id'], df_history['booking_id']]).dropna().astype(str))
    numeric_ids = {int(id_str) for id_str in all_ids if id_str.isdigit()}
    return f"{max(numeric_ids) + 1:03d}" if numeric_ids else "001"

init_app()

# ===================================================================
# PAPARAN UTAMA
# ===================================================================
st.title("💈 MEGAT BARBER")
tab_customer, tab_barber = st.tabs(["👥 PORTAL PELANGGAN", "✂️ DASHBOARD BARBER"])

# -------------------------------------------------------------------
# TAB PORTAL PELANGGAN
# -------------------------------------------------------------------
with tab_customer:
    col1, col2, col3 = st.columns(3)
    col1.link_button("📷 Instagram", "https://instagram.com/mgatirfan", use_container_width=True)
    col2.link_button("🎵 TikTok", "https://tiktok.com/@megatirfan_", use_container_width=True)
    col3.link_button("💬 WhatsApp", f"https://wa.me/{BARBER_WHATSAPP}", use_container_width=True)
    st.divider()

    st.subheader("📸 Portfolio")
    portfolio_folder = "portfolio"
    if os.path.exists(portfolio_folder) and os.path.isdir(portfolio_folder):
        images = [f for f in os.listdir(portfolio_folder) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
        if images:
            cols = st.columns(min(len(images), 3)); [cols[i % 3].image(os.path.join(portfolio_folder, img), use_container_width=True) for i, img in enumerate(images)]
    st.divider()

    col_book, col_walkin = st.columns(2)
    with col_book:
        st.header("📅 Tempah Slot")
        with st.form("booking_form", clear_on_submit=True):
            name = st.text_input("Nama Anda"); phone = st.text_input("Nombor Telefon")
            service = st.selectbox("Pilih Servis", ["Smart Cut", "Fade", "Haircut + Beard", "Beard Trim"])
            SERVICE_PRICE = {"Smart Cut": 15, "Fade": 25, "Haircut + Beard": 35, "Beard Trim": 10}
            slot_df = read_csv("availability").dropna()
            if not slot_df.empty:
                slot_df['datetime'] = pd.to_datetime(slot_df['date'] + ' ' + slot_df['time'], errors='coerce')
                future_slots_df = slot_df[slot_df['datetime'] > datetime.now()].copy()
                future_slots_df['option_label'] = future_slots_df['date'].astype(str) + " | " + future_slots_df['time'].astype(str)
                slot_options = future_slots_df['option_label'].tolist()
            else:
                slot_options = []
            selected_slot = st.selectbox("Pilih Slot Tersedia (Slot Lalu Disembunyikan)", slot_options, disabled=(not slot_options))
            if st.form_submit_button("Hantar Tempahan", use_container_width=True, disabled=(not slot_options)):
                if name and phone:
                    booking_id = generate_unique_booking_id()
                    new_booking = pd.DataFrame([[booking_id, datetime.now().strftime("%Y-%m-%d"), name, phone, service, selected_slot, SERVICE_PRICE.get(service, 0), "Pending"]], columns=COLUMNS["bookings"])
                    pd.concat([read_csv("bookings"), new_booking], ignore_index=True).to_csv(FILES["bookings"], index=False)
                    parts = selected_slot.split(" | "); slot_df[~((slot_df["date"] == parts[0]) & (slot_df["time"] == parts[1]))].to_csv(FILES["availability"], index=False)
                    st.success(f"✅ Tempahan Berjaya! ID Anda: **{booking_id}**")
                    whatsapp_message = f"Hai Megat Barber, saya {name} ingin mengesahkan tempahan ID: {booking_id} untuk slot {selected_slot}."
                    st.link_button("📲 Hantar Pengesahan ke WhatsApp", f"https://wa.me/{BARBER_WHATSAPP}?text={quote(whatsapp_message)}", use_container_width=True)
                else: st.error("Sila isi nama dan nombor telefon.")
    with col_walkin:
        st.header("🚶 Daftar Walk-In")
        with st.form("walkin_form", clear_on_submit=True):
            walkin_name = st.text_input("Nama Anda")
            if st.form_submit_button("Dapatkan Nombor Giliran", use_container_width=True):
                if walkin_name:
                    walkin_df = read_csv("walkin"); last_id = pd.to_numeric(walkin_df['queue_id'], errors='coerce').max()
                    queue_id = f"{int(last_id) + 1:02d}" if pd.notna(last_id) else "01"
                    pd.concat([walkin_df, pd.DataFrame([[queue_id, walkin_name, "Waiting"]], columns=COLUMNS["walkin"])], ignore_index=True).to_csv(FILES["walkin"], index=False)
                    st.success(f"🎟️ Pendaftaran Berjaya! No Giliran Anda: {queue_id}")
                else: st.error("Sila masukkan nama anda.")
    st.divider()

    st.subheader("🔍 Urus Janji Temu Anda")
    with st.expander("Urus Tempahan (Booking) Anda"):
        check_id = st.text_input("Masukkan Booking ID Anda", key="customer_booking_id")
        col_check, col_cancel = st.columns(2)
        with col_check:
            if st.button("Semak Status Booking", use_container_width=True, key="customer_check_booking"):
                if check_id:
                    found = False
                    for file_key, category in [("bookings", "Semasa"), ("history", "Arkib")]:
                        df = read_csv(file_key); match = df[df["booking_id"].astype(str) == check_id]
                        if not match.empty: st.info(f"Status {category}: **{match.iloc[0]['status']}**"); found = True; break
                    if not found: st.error("Booking ID tidak ditemui.")
                else: st.warning("Sila masukkan Booking ID.")
        with col_cancel:
            if st.button("Batalkan Booking Ini", use_container_width=True, type="primary", key="customer_cancel_booking"):
                if check_id:
                    df_b = read_csv("bookings"); match = df_b[df_b["booking_id"].astype(str) == check_id]
                    if not match.empty:
                        cancelled_row = match.copy(); cancelled_row['status'] = 'Cancelled'
                        pd.concat([read_csv("history"), cancelled_row], ignore_index=True).to_csv(FILES["history"], index=False)
                        df_b[df_b["booking_id"].astype(str) != check_id].to_csv(FILES["bookings"], index=False)
                        slot_val = str(match.iloc[0]['slot']); parts = slot_val.split(" | ")
                        if len(parts) == 2:
                            pd.concat([read_csv("availability"), pd.DataFrame([parts], columns=['date', 'time'])], ignore_index=True).sort_values(['date', 'time']).drop_duplicates().to_csv(FILES["availability"], index=False)
                        st.success(f"Tempahan ID {check_id} berjaya dibatalkan.")
                    else: st.error("Booking ID aktif tidak ditemui.")
                else: st.warning("Sila masukkan Booking ID.")
    with st.expander("Batalkan Giliran Walk-In Anda"):
        walkin_id_to_cancel = st.text_input("Masukkan Nombor Giliran Walk-In Anda", key="customer_walkin_id")
        if st.button("Batalkan Giliran Walk-In", use_container_width=True, type="primary", key="customer_cancel_walkin"):
            if walkin_id_to_cancel:
                df_w = read_csv("walkin"); df_w['queue_id'] = df_w['queue_id'].astype(str)
                if walkin_id_to_cancel in df_w['queue_id'].values:
                    df_w[df_w["queue_id"] != walkin_id_to_cancel].to_csv(FILES["walkin"], index=False)
                    st.success(f"Giliran Walk-in No. {walkin_id_to_cancel} telah berjaya dibatalkan.")
                else: st.error("Nombor Giliran Walk-In tidak ditemui.")
            else: st.warning("Sila masukkan Nombor Giliran.")

# -------------------------------------------------------------------
# TAB DASHBOARD BARBER
# -------------------------------------------------------------------
with tab_barber:
    if not st.session_state.get('logged_in'):
        st.header("✂️ Log Masuk Pengurusan Barber")
        password = st.text_input("Masukkan Password Admin", type="password", key="admin_password")
        if st.button("Log Masuk", use_container_width=True):
            if password == BARBER_PASSWORD: st.session_state.logged_in = True; st.rerun()
            else: st.error("Kata laluan salah.")
    else:
        st.subheader("👑 Dashboard Admin")
        if st.button("Log Keluar", use_container_width=True, type="primary"): st.session_state.logged_in = False; st.rerun()
        st.divider()

        df_bookings, df_walkin, df_history, df_availability = read_csv("bookings"), read_csv("walkin"), read_csv("history"), read_csv("availability")

        st.subheader("📊 Ringkasan Prestasi"); col1, col2, col3 = st.columns(3); col1.metric("📋 Tempahan Aktif", len(df_bookings))
        col2.metric("🚶 Walk-In Menunggu", len(df_walkin)); completed_income = pd.to_numeric(df_history[df_history["status"] == "Completed"]["price"], errors='coerce').sum()
        col3.metric("💰 Jumlah Pendapatan", f"RM {completed_income:.2f}"); st.divider()

        with st.expander("📊 Buka Laporan Analitik & Prestasi"):
            st.markdown("#### Analitik Perniagaan")
            if not df_history.empty and 'status' in df_history.columns:
                completed_df = df_history[df_history['status'] == 'Completed'].copy()
                if not completed_df.empty:
                    col_chart1, col_chart2 = st.columns(2)
                    with col_chart1:
                        st.markdown("##### Servis Paling Laris"); service_counts = completed_df['service'].value_counts()
                        st.bar_chart(service_counts)
                    with col_chart2:
                        st.markdown("##### Trend Pendapatan Harian"); completed_df['date'] = pd.to_datetime(completed_df['date'], errors='coerce')
                        income_trend = completed_df.groupby(completed_df['date'].dt.date)['price'].sum()
                        st.line_chart(income_trend)
                    st.markdown("---")
                    st.markdown("##### 📜 **Data Rujukan Sejarah (History)**")
                    st.dataframe(df_history, use_container_width=True)
                else: st.info("Tiada data 'Completed' untuk dipaparkan dalam graf.")
            else: st.info("Tiada data sejarah (history) untuk dianalisis.")
        st.divider()

        st.subheader("🗓️ Urus Slot Masa"); st.dataframe(df_availability.sort_values(["date", "time"]), use_container_width=True)
        with st.expander("➕ Tambah atau ➖ Padam Slot"):
            col1, col2 = st.columns(2)
            with col1:
                with st.form("add_slot_form"):
                    st.markdown("##### Tambah Slot Baru"); new_date, new_time = st.date_input("Pilih Tarikh"), st.time_input("Pilih Masa")
                    if st.form_submit_button("Simpan Slot", use_container_width=True):
                        new_slot_df = pd.DataFrame([[new_date.strftime('%Y-%m-%d'), new_time.strftime('%H:%M')]], columns=['date', 'time'])
                        pd.concat([df_availability, new_slot_df]).drop_duplicates().sort_values(["date", "time"]).to_csv(FILES["availability"], index=False)
                        st.success("Slot berjaya ditambah!"); st.rerun()
            with col2:
                if not df_availability.empty:
                    st.markdown("##### Padam Slot Sedia Ada"); options = (df_availability['date'].astype(str) + " | " + df_availability['time'].astype(str)).tolist()
                    slot_to_delete = st.selectbox("Pilih slot untuk dipadam", options, key="delete_slot_select")
                    if st.button("Padam Slot Ini", use_container_width=True, type="primary"):
                        parts = slot_to_delete.split(" | "); df_availability[~((df_availability['date'] == parts[0]) & (df_availability['time'] == parts[1]))].to_csv(FILES["availability"], index=False)
                        st.success("Slot berjaya dipadam!"); st.rerun()
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 Urus Tempahan"); st.markdown("**Tempahan Hari Ini**"); today_str = datetime.now().strftime('%Y-%m-%d')
            st.dataframe(df_bookings[df_bookings['slot'].astype(str).str.startswith(today_str, na=False)], use_container_width=True); st.markdown("**Semua Tempahan Aktif**"); st.dataframe(df_bookings, use_container_width=True)
            if not df_bookings.empty:
                with st.expander("✏️ Kemaskini Status Tempahan"):
                    idx_to_update = st.selectbox("Pilih tempahan", df_bookings.index, format_func=lambda x: f"ID {df_bookings.loc[x, 'booking_id']}", key="update_booking_select")
                    new_status = st.selectbox("Tukar status kepada", ["Pending", "Confirmed", "On Going", "Completed", "Cancelled"], key="booking_status")
                    if st.button("Kemaskini Tempahan", use_container_width=True):
                        row = df_bookings.loc[idx_to_update].copy(); row['status'] = new_status
                        if new_status in ["Completed", "Cancelled"]: pd.concat([df_history, pd.DataFrame([row])]).to_csv(FILES["history"], index=False); df_bookings.drop(idx_to_update).reset_index(drop=True).to_csv(FILES["bookings"], index=False)
                        else: df_bookings.loc[idx_to_update, 'status'] = new_status; df_bookings.to_csv(FILES["bookings"], index=False)
                        st.success("Status tempahan dikemaskini."); st.rerun()
        with col2:
            st.subheader("🚶 Urus Walk-In"); st.dataframe(df_walkin, use_container_width=True)
            if not df_walkin.empty:
                with st.expander("✏️ Kemaskini Pelanggan Walk-In"):
                    walkin_idx = st.selectbox("Pilih pelanggan", df_walkin.index, format_func=lambda x: f"No. {df_walkin.loc[x, 'queue_id']}", key="walkin_select")
                    action_cols = st.columns(2)
                    with action_cols[0]:
                        new_walkin_status = st.selectbox("Tukar status", ["Waiting", "On Going"], key="walkin_status_select")
                        if st.button("Kemaskini Status", use_container_width=True):
                            df_walkin.loc[walkin_idx, 'status'] = new_walkin_status; df_walkin.to_csv(FILES["walkin"], index=False)
                            st.success("Status walk-in dikemaskini."); st.rerun()
                    with action_cols[1]:
                        if st.button("Tandakan Selesai", use_container_width=True):
                            df_walkin.drop(walkin_idx).reset_index(drop=True).to_csv(FILES["walkin"], index=False)
                            st.success("Walk-in ditandakan selesai."); st.rerun()
                        if st.button("Batalkan Walk-In", use_container_width=True, type="primary"):
                            cancelled_id = df_walkin.loc[walkin_idx, 'queue_id']
                            df_walkin.drop(walkin_idx).reset_index(drop=True).to_csv(FILES["walkin"], index=False)
                            st.success(f"Walk-in No. {cancelled_id} dibatalkan."); st.rerun()


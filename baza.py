import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
# Dane pobierane ze Streamlit Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Supabase", layout="wide")
st.title("📦 Zarządzanie Produktami i Kategoriami")

# --- SEKCJA 1: DODAWANIE KATEGORII ---
st.header("1. Dodaj Nową Kategorię")
with st.form("form_kategorie", clear_on_submit=True):
    kat_nazwa = st.text_input("Nazwa kategorii")
    kat_opis = st.text_area("Opis kategorii")
    submit_kat = st.form_submit_button("Zapisz kategorię")

    if submit_kat:
        if kat_nazwa:
            try:
                data = {"nazwa": kat_nazwa, "opis": kat_opis}
                supabase.table("kategorie").insert(data).execute()
                st.success(f"Dodano kategorię: {kat_nazwa}")
            except Exception as e:
                st.error(f"Błąd: {e}")
        else:
            st.error("Nazwa kategorii jest wymagana!")

# --- SEKCJA 2: DODAWANIE PRODUKTU ---
st.header("2. Dodaj Nowy Produkt")

# Pobranie aktualnych kategorii
categories_query = supabase.table("kategorie").select("id, nazwa").execute()
categories_list = categories_query.data
cat_options = {c['nazwa']: c['id'] for c in categories_list}

with st.form("form_produkty", clear_on_submit=True):
    prod_nazwa = st.text_input("Nazwa produktu")
    prod_liczba = st.number_input("Liczba (szt.)", min_value=0, step=1)
    prod_cena = st.number_input("Cena", min_value=0.0, format="%.2f")
    
    selected_cat_name = st.selectbox(
        "Wybierz kategorię", 
        options=list(cat_options.keys()) if cat_options else ["Brak kategorii - dodaj ją najpierw"]
    )
    
    submit_prod = st.form_submit_button("Zapisz produkt")

    if submit_prod:
        if prod_nazwa and cat_options:
            try:
                product_data = {
                    "nazwa": prod_nazwa,
                    "liczba": prod_liczba,
                    "cena": prod_cena,
                    "kategoria_id": cat_options[selected_cat_name]
                }
                supabase.table("produkty").insert(product_data).execute()
                st.success(f"Dodano produkt: {prod_nazwa}")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd: {e}")
        else:
            st.error("Wypełnij wymagane pola!")

st.divider()

# --- SEKCJA 3: PODGLĄD I EDYCJA ---
st.header("3. Twoje Produkty")

# Pobieramy dane
res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
products_data = res.data

if products_data:
    # Wyświetlenie tabeli
    display_data = []
    for p in products_data:
        display_data.append({
            "ID": p['id'],
            "Nazwa": p['nazwa'],
            "Ilość": p['liczba'],
            "Cena": p['cena'],
            "Kategoria": p['kategorie']['nazwa'] if p['kategorie'] else "Brak"
        })
    st.dataframe(display_data, use_container_width=True)

    # --- PODSEKCJA: ZMIANA ILOŚCI ---
    st.subheader("🔄 Szybka zmiana ilości")
    col_upd1, col_upd2, col_upd3 = st.columns([2, 1, 1])
    
    # Mapowanie do selectboxa
    product_map = {f"{p['nazwa']} (Obecnie: {p['liczba']})": p for p in products_data}
    
    with col_upd1:
        selected_prod_text = st.selectbox("Wybierz produkt do edycji", options=list(product_map.keys()), key="update_select")
        selected_prod = product_map[selected_prod_text]
        
    with col_upd2:
        new_quantity = st.number_input("Nowa ilość", min_value=0, value=int(selected_prod['liczba']), step=1)
        
    with col_upd3:
        st.write(" ") # wyrównanie
        if st.button("Zaktualizuj ilość", use_container_width=True):
            supabase.table("produkty").update({"liczba": new_quantity}).eq("id", selected_prod['id']).execute()
            st.success("Zaktualizowano!")
            st.rerun()

    # --- PODSEKCJA: USUWANIE ---
    st.subheader("🗑️ Usuwanie produktu")
    col_del1, col_del2 = st.columns([3, 1])
    
    with col_del1:
        delete_map = {f"{p['nazwa']} (ID: {p['id']})": p['id'] for p in products_data}
        to_delete = st.selectbox("Wybierz produkt do usunięcia", options=list(delete_map.keys()), key="delete_select")
    
    with col_del2:
        st.write(" ")
        if st.button("USUŃ DEFINITYWNIE", type="primary", use_container_width=True):
            target_id = delete_map[to_delete]
            supabase.table("produkty").delete().eq("id", target_id).execute()
            st.warning("Produkt usunięty!")
            st.rerun()

else:
    st.info("Baza produktów jest pusta.")

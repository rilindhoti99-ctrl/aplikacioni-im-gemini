import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
import google.generativeai as genai

# --- KONFIGURIMI I FAQES ---
st.set_page_config(page_title="AGROLINDI RH", page_icon="🚜", layout="wide")

# --- MENAXHIMI I TË DHËNAVE (DATABASE JSON) ---
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

FILES = {
    "products": os.path.join(DATA_DIR, "products.json"),
    "sales": os.path.join(DATA_DIR, "sales.json"),
    "supplies": os.path.join(DATA_DIR, "supplies.json"),
    "debts": os.path.join(DATA_DIR, "debts.json"),
    "categories": os.path.join(DATA_DIR, "categories.json")
}

# Funksione për Load/Save
def load_data(key, default=[]):
    if os.path.exists(FILES[key]):
        with open(FILES[key], 'r') as f:
            return json.load(f)
    return default

def save_data(key, data):
    with open(FILES[key], 'w') as f:
        json.dump(data, f, indent=4)

# Inizializimi i Session State
if 'cart' not in st.session_state:
    st.session_state['cart'] = []

# --- LOGJIKA KRYESORE (FIFO & STOKU) ---
def update_stock_fifo(product_id, qty_sold):
    products = load_data("products")
    for p in products:
        if p['id'] == product_id:
            # Zbrit stokun total
            p['stock'] -= qty_sold
            
            # FIFO LOGIC: Zbrit nga batches (Furnizimet e vjetra)
            qty_needed = qty_sold
            new_batches = []
            # Rendit sipas datës (më e vjetra para)
            batches = sorted(p.get('batches', []), key=lambda x: x['date'])
            
            for batch in batches:
                if qty_needed <= 0:
                    new_batches.append(batch)
                    continue
                
                if batch['quantity'] > qty_needed:
                    batch['quantity'] -= qty_needed
                    qty_needed = 0
                    new_batches.append(batch)
                else:
                    qty_needed -= batch['quantity']
                    # Batch u zbraz, nuk e shtojmë në listë
            
            p['batches'] = new_batches
            break
    save_data("products", products)

def calculate_profit(sale_items):
    # Kjo funksionon duke supozuar koston mesatare ose aktuale
    # Për saktësi 100% duhet gjurmuar kostoja e saktë nga batch gjatë FIFO
    # Këtu përdorim 'purchasePrice' aktual të produktit për thjeshtësi në UI
    products = load_data("products")
    cost = 0
    revenue = 0
    for item in sale_items:
        prod = next((p for p in products if p['id'] == item['product_id']), None)
        if prod:
            revenue += item['price'] * item['quantity']
            cost += prod.get('purchasePrice', 0) * item['quantity']
    return revenue, cost, revenue - cost

# --- NDËRFAQJA (UI) ---

# Sidebar Navigation
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/862/862832.png", width=100)
st.sidebar.title("AGROLINDI RH")
menu = st.sidebar.radio("Navigimi", ["Dashboard", "Inventari", "Furnizimet", "Shitjet (POS)", "Borxhet", "Raportet", "Asistenti AI"])

# 1. DASHBOARD
if menu == "Dashboard":
    st.title("📊 Paneli Kryesor")
    
    products = load_data("products")
    sales = load_data("sales")
    
    # KPIs
    total_sales = sum(s['total'] for s in sales)
    total_orders = len(sales)
    low_stock = [p for p in products if p['stock'] < 5]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Totali Shitjeve", f"{total_sales:,.2f} €", delta="Totale")
    c2.metric("Porosi", total_orders, delta="Fatura")
    c3.metric("Produkte në Stok", len(products))
    c4.metric("Stok Kritik", len(low_stock), delta_color="inverse")
    
    if low_stock:
        st.warning(f"⚠️ Kujdes! {len(low_stock)} produkte janë duke mbaruar.")
        with st.expander("Shiko Produktet me Stok të Ulët"):
            st.dataframe(pd.DataFrame(low_stock)[['name', 'stock', 'category']])

    # Charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Shitjet Ditore (7 Ditët e Fundit)")
        if sales:
            df_sales = pd.DataFrame(sales)
            df_sales['date'] = pd.to_datetime(df_sales['date']).dt.date
            daily_sales = df_sales.groupby('date')['total'].sum().reset_index()
            fig = px.bar(daily_sales, x='date', y='total', labels={'total': 'Euro', 'date': 'Data'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("S'ka të dhëna shitjesh.")

    with col_chart2:
        st.subheader("Top Produkte")
        if sales:
            all_items = []
            for s in sales:
                for item in s['items']:
                    all_items.append(item)
            df_items = pd.DataFrame(all_items)
            if not df_items.empty:
                # Duhet marrë emri produktit bazuar në ID
                top_prods = df_items.groupby('product_id')['quantity'].sum().reset_index().sort_values('quantity', ascending=False).head(5)
                # Map names
                top_prods['name'] = top_prods['product_id'].apply(lambda x: next((p['name'] for p in products if p['id'] == x), "Unknown"))
                fig2 = px.pie(top_prods, values='quantity', names='name', hole=0.4)
                st.plotly_chart(fig2, use_container_width=True)

# 2. INVENTARI
elif menu == "Inventari":
    st.title("📦 Inventari i Dyqanit")
    
    products = load_data("products")
    categories = load_data("categories", [{"name": "Koncentrat", "icon": "🐄"}, {"name": "Fara", "icon": "🌱"}])
    
    # Tabs
    tab1, tab2 = st.tabs(["Lista e Produkteve", "Shto Produkt / Kategori"])
    
    with tab1:
        search = st.text_input("Kërko produkt...", "")
        df_prod = pd.DataFrame(products)
        
        if not df_prod.empty:
            if search:
                df_prod = df_prod[df_prod['name'].str.contains(search, case=False)]
            
            # Shfaqja
            st.dataframe(
                df_prod[['name', 'category', 'price', 'purchasePrice', 'stock', 'description']],
                column_config={
                    "name": "Emri",
                    "category": "Kategoria",
                    "price": st.column_config.NumberColumn("Shitja (€)", format="%.2f €"),
                    "purchasePrice": st.column_config.NumberColumn("Blerja (€)", format="%.2f €"),
                    "stock": "Stoku",
                    "description": "Përshkrimi"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nuk keni produkte akoma.")

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Shto Produkt të Ri")
            with st.form("add_product_form"):
                p_name = st.text_input("Emri Produktit")
                p_cat = st.selectbox("Kategoria", [c['name'] for c in categories])
                p_price = st.number_input("Çmimi Shitjes", min_value=0.0, step=0.1)
                p_cost = st.number_input("Çmimi Blerjes (Kosto)", min_value=0.0, step=0.1)
                p_stock = st.number_input("Stoku Fillestar", min_value=0, step=1)
                p_desc = st.text_area("Përshkrimi")
                
                if st.form_submit_button("Ruaj Produktin"):
                    new_prod = {
                        "id": str(datetime.now().timestamp()),
                        "name": p_name,
                        "category": p_cat,
                        "price": p_price,
                        "purchasePrice": p_cost,
                        "stock": p_stock,
                        "description": p_desc,
                        "batches": [{
                            "id": f"batch_{datetime.now().timestamp()}",
                            "date": datetime.now().isoformat(),
                            "quantity": p_stock,
                            "cost": p_cost
                        }]
                    }
                    products.append(new_prod)
                    save_data("products", products)
                    st.success("Produkti u shtua!")
                    st.rerun()

# 3. FURNIZIMET
elif menu == "Furnizimet":
    st.title("🚚 Furnizimet (Hyrje Malli)")
    
    with st.form("supply_form"):
        col1, col2 = st.columns(2)
        with col1:
            s_supplier = st.text_input("Furnitori (Kompania)")
            s_item = st.text_input("Emri Mallit")
            s_cat = st.text_input("Kategoria")
        with col2:
            s_qty = st.number_input("Sasia", min_value=1)
            s_buy_price = st.number_input("Çmimi Blerjes (€)", min_value=0.0)
            s_sell_price = st.number_input("Çmimi Shitjes (€)", min_value=0.0)
        
        if st.form_submit_button("Regjistro Furnizimin"):
            supplies = load_data("supplies")
            products = load_data("products")
            
            # 1. Regjistro Supply
            new_supply = {
                "id": str(datetime.now().timestamp()),
                "date": datetime.now().isoformat(),
                "supplier": s_supplier,
                "itemName": s_item,
                "category": s_cat,
                "purchasePrice": s_buy_price,
                "sellingPrice": s_sell_price,
                "quantity": s_qty
            }
            supplies.append(new_supply)
            save_data("supplies", supplies)
            
            # 2. Update ose Krijo Produkt
            existing_prod = next((p for p in products if p['name'].lower() == s_item.lower()), None)
            
            new_batch = {
                "id": f"batch_{datetime.now().timestamp()}",
                "date": datetime.now().isoformat(),
                "quantity": s_qty,
                "cost": s_buy_price
            }
            
            if existing_prod:
                existing_prod['stock'] += s_qty
                existing_prod['price'] = s_sell_price
                existing_prod['purchasePrice'] = s_buy_price
                if 'batches' not in existing_prod: existing_prod['batches'] = []
                existing_prod['batches'].append(new_batch)
            else:
                new_prod = {
                    "id": str(datetime.now().timestamp()),
                    "name": s_item,
                    "category": s_cat,
                    "price": s_sell_price,
                    "purchasePrice": s_buy_price,
                    "stock": s_qty,
                    "description": f"Furnizim nga {s_supplier}",
                    "batches": [new_batch]
                }
                products.append(new_prod)
            
            save_data("products", products)
            st.success("Furnizimi u regjistrua dhe stoku u përditësua!")

# 4. SHITJET (POS)
elif menu == "Shitjet (POS)":
    st.title("🛒 Kasa & Shitjet")
    
    products = load_data("products")
    
    col_prod, col_cart = st.columns([2, 1])
    
    with col_prod:
        st.subheader("Zgjidh Produkte")
        # Searchable dropdown
        prod_names = [f"{p['name']} ({p['stock']} copë) - {p['price']}€" for p in products if p['stock'] > 0]
        selected_label = st.selectbox("Kërko Produktin", [""] + prod_names)
        
        qty = st.number_input("Sasia", min_value=1, value=1)
        
        if st.button("Shto në Shportë"):
            if selected_label:
                # Extract product data
                p_name = selected_label.split(" (")[0]
                product = next(p for p in products if p['name'] == p_name)
                
                if qty > product['stock']:
                    st.error("Nuk ka stok të mjaftueshëm!")
                else:
                    # Add to session cart
                    cart_item = {
                        "product_id": product['id'],
                        "name": product['name'],
                        "price": product['price'],
                        "quantity": qty,
                        "total": qty * product['price']
                    }
                    st.session_state['cart'].append(cart_item)
                    st.success(f"{p_name} u shtua!")

    with col_cart:
        st.subheader("🧾 Shporta")
        cart_df = pd.DataFrame(st.session_state['cart'])
        
        if not cart_df.empty:
            st.dataframe(cart_df[['name', 'quantity', 'total']], hide_index=True)
            grand_total = cart_df['total'].sum()
            st.divider()
            st.metric("TOTALI", f"{grand_total:.2f} €")
            
            # DEBT OPTION
            is_debt = st.checkbox("Shitje me Borxh?")
            debtor_name = ""
            is_agreement = False
            due_date = None
            
            if is_debt:
                st.info("Regjistrimi i Borxhit")
                debtor_name = st.text_input("Emri i Klientit")
                is_agreement = st.checkbox("Me Marrëveshje?")
                due_date = st.date_input("Data e Premtimit Pagesës")
            
            if st.button("Përfundo Shitjen", type="primary"):
                if is_debt and not debtor_name:
                    st.error("Shkruani emrin e klientit!")
                else:
                    # 1. Save Sale
                    sales = load_data("sales")
                    new_sale = {
                        "id": str(datetime.now().timestamp()),
                        "date": datetime.now().isoformat(),
                        "items": st.session_state['cart'],
                        "total": grand_total,
                        "type": "debt" if is_debt else "cash"
                    }
                    sales.append(new_sale)
                    save_data("sales", sales)
                    
                    # 2. Update Stock (FIFO)
                    for item in st.session_state['cart']:
                        update_stock_fifo(item['product_id'], item['quantity'])
                    
                    # 3. Add to Debts if needed
                    if is_debt:
                        debts = load_data("debts")
                        debts.append({
                            "id": str(datetime.now().timestamp()),
                            "personName": debtor_name,
                            "amount": grand_total,
                            "dateTaken": datetime.now().isoformat(),
                            "description": ", ".join([f"{i['quantity']}x {i['name']}" for i in st.session_state['cart']]),
                            "isPaid": False,
                            "hasAgreement": is_agreement,
                            "paymentDueDate": due_date.isoformat() if due_date else None,
                            "history": []
                        })
                        save_data("debts", debts)
                    
                    # Reset
                    st.session_state['cart'] = []
                    st.success("Shitja u krye me sukses!")
                    st.rerun()
                    
            if st.button("Pastro Shportën"):
                st.session_state['cart'] = []
                st.rerun()
        else:
            st.write("Shporta është bosh.")

# 5. BORXHET
elif menu == "Borxhet":
    st.title("📒 Libri i Borxhlive")
    
    debts = load_data("debts")
    if not debts:
        st.info("Nuk ka borxhlinj.")
    else:
        # Filter Logic
        filter_type = st.radio("Filtro:", ["Të Gjitha", "Aktive", "Me Marrëveshje"])
        
        display_debts = debts
        if filter_type == "Aktive":
            display_debts = [d for d in debts if not d['isPaid'] and d['amount'] > 0]
        elif filter_type == "Me Marrëveshje":
            display_debts = [d for d in debts if d.get('hasAgreement')]
            
        for debt in display_debts:
            if debt['amount'] <= 0 and not debt['isPaid']:
                continue # Skip fully paid hidden ones if needed
                
            # Card UI
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 2])
                
                # Check overdue
                is_overdue = False
                days_overdue = 0
                if debt.get('paymentDueDate'):
                    due = datetime.fromisoformat(debt['paymentDueDate'])
                    if datetime.now() > due and not debt['isPaid']:
                        is_overdue = True
                        days_overdue = (datetime.now() - due).days
                
                bg_color = "🔴" if is_overdue else ("🟣" if debt.get('hasAgreement') else "🔵")
                
                with col1:
                    st.subheader(f"{bg_color} {debt['personName']}")
                    st.caption(f"Data: {debt['dateTaken'][:10]}")
                    if is_overdue:
                        st.error(f"⚠️ Vonesë: {days_overdue} ditë!")
                
                with col2:
                    st.metric("Borxhi Mbetur", f"{debt['amount']:.2f} €")
                
                with col3:
                    # Partial Payment Form
                    with st.expander("Paguaj"):
                        pay_amt = st.number_input(f"Shuma për {debt['personName']}", min_value=0.0, max_value=float(debt['amount']), key=debt['id'])
                        if st.button("Konfirmo Pagesën", key=f"btn_{debt['id']}"):
                            if pay_amt > 0:
                                debt['amount'] -= pay_amt
                                history_entry = f"[{datetime.now().strftime('%Y-%m-%d')}] Paguar: {pay_amt}€, Mbetja: {debt['amount']}€"
                                
                                if 'history' not in debt: debt['history'] = []
                                debt['history'].append(history_entry)
                                debt['description'] += f"\n{history_entry}"
                                
                                if debt['amount'] <= 0.01:
                                    debt['isPaid'] = True
                                    debt['amount'] = 0
                                
                                save_data("debts", debts)
                                st.success("Pagesa u regjistrua!")
                                st.rerun()
                st.divider()

# 6. RAPORTET
elif menu == "Raportet":
    st.title("📈 Raportet Financiare")
    
    sales = load_data("sales")
    supplies = load_data("supplies")
    
    date_filter = st.date_input("Zgjidh Datën", datetime.now())
    selected_date_str = date_filter.strftime("%Y-%m-%d")
    
    # Filter data
    day_sales = [s for s in sales if s['date'].startswith(selected_date_str)]
    day_supplies = [s for s in supplies if s['date'].startswith(selected_date_str)]
    
    total_revenue = sum(s['total'] for s in day_sales)
    total_cost = sum(s['purchasePrice'] * s['quantity'] for s in day_supplies) # Kjo është shpenzim blerje, jo kosto e shitjes (COGS)
    
    # Për fitim real duhet llogaritur marzhi i shitjes
    profit_estimate = 0
    for sale in day_sales:
        rev, cost, prof = calculate_profit(sale['items'])
        profit_estimate += prof
        
    c1, c2, c3 = st.columns(3)
    c1.metric("Xhiro Ditore (Hyrje)", f"{total_revenue:.2f} €")
    c2.metric("Shpenzime Malli (Dalje)", f"{total_cost:.2f} €")
    c3.metric("Fitimi Neto (Vlerësim)", f"{profit_estimate:.2f} €", delta_color="normal")
    
    st.subheader("Detajet e Shitjeve Sot")
    if day_sales:
        st.dataframe(pd.DataFrame(day_sales)[['date', 'total', 'type']])

# 7. ASISTENTI AI
elif menu == "Asistenti AI":
    st.title("🤖 Asistenti Inteligjent (Gemini)")
    
    # API Key Setup
    api_key = st.text_input("Shkruani Google Gemini API Key", type="password")
    
    if api_key:
        genai.configure(api_key=api_key)
        
        # Përgatitja e kontekstit
        products = load_data("products")
        sales = load_data("sales")
        context = f"""
        Ti je asistenti i dyqanit bujqësor AGROLINDI RH.
        Të dhënat aktuale:
        - Produktet: {len(products)} gjithsej.
        - Shitjet totale historike: {len(sales)} fatura.
        - Produkte stok kritik: {[p['name'] for p in products if p['stock'] < 5]}
        
        Përgjigju pyetjeve të përdoruesit në shqip rreth biznesit.
        """
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Pyet diçka (psh: Cilat produkte po mbarojnë?)"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                model = genai.GenerativeModel("gemini-pro")
                full_prompt = f"{context}\nUser: {prompt}\nAI:"
                response = model.generate_content(full_prompt)
                
                with st.chat_message("assistant"):
                    st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Gabim me AI: {e}")
    else:
        st.warning("Ju lutem vendosni API Key për të vazhduar.")

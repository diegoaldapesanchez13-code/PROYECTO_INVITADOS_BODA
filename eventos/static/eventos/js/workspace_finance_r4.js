(() => {
"use strict";
function openDialog(d){ if(!d)return; if(typeof d.showModal==="function") d.showModal(); else d.setAttribute("open","");}
function init(){
 const root=document.querySelector("[data-finance-workspace]"); if(!root||root.dataset.ready==="1")return; root.dataset.ready="1";
 const by=(n)=>root.querySelector(`[data-dialog="${n}"]`);
 root.querySelectorAll("[data-finance-open]").forEach(b=>b.addEventListener("click",()=>openDialog(by(b.dataset.financeOpen))));
 const edit=by("edit-expense"), editForm=edit?.querySelector("[data-edit-expense-form]");
 root.querySelectorAll("[data-edit-expense]").forEach(b=>b.addEventListener("click",()=>{
   if(!editForm)return; editForm.action=b.dataset.action;
   const map={servicio_evento:b.dataset.servicio,categoria:b.dataset.categoria,proveedor:b.dataset.proveedor,concepto:b.dataset.concepto,monto_estimado:b.dataset.estimado,monto_real:b.dataset.real,fecha_limite:b.dataset.fecha,notas:b.dataset.notas};
   Object.entries(map).forEach(([n,v])=>{const el=editForm.elements.namedItem(n); if(el)el.value=v||"";}); openDialog(edit);
 }));
 const pay=by("pay-expense"), payForm=pay?.querySelector("[data-pay-form]");
 root.querySelectorAll("[data-pay-expense]").forEach(b=>b.addEventListener("click",()=>{
   if(!payForm)return; payForm.action=b.dataset.action; payForm.reset(); const amount=payForm.elements.namedItem("monto"); if(amount)amount.max=b.dataset.saldo||"";
   const copy=pay.querySelector("[data-pay-copy]"); if(copy)copy.textContent=`${b.dataset.title} · saldo pendiente $${b.dataset.saldo}`; openDialog(pay);
 }));
 const life=by("life-expense"), lifeForm=life?.querySelector("[data-life-form]");
 root.querySelectorAll("[data-life-expense]").forEach(b=>b.addEventListener("click",()=>{
   if(!lifeForm)return; lifeForm.action=b.dataset.action; lifeForm.reset(); const cancel=b.dataset.mode==="cancel";
   life.querySelector("[data-life-title]").textContent=cancel?"Cancelar gasto":"Archivar gasto";
   life.querySelector("[data-life-copy]").textContent=cancel?`Cancelar “${b.dataset.title}” lo excluirá de los totales activos. Si tiene pagos activos primero deben anularse.`:`Archivar “${b.dataset.title}” lo moverá al historial sin alterar sus movimientos financieros.`;
   life.querySelector("[data-life-submit]").textContent=cancel?"Cancelar gasto":"Archivar gasto"; openDialog(life);
 }));
 const annul=by("annul-payment"), annulForm=annul?.querySelector("[data-annul-form]");
 root.querySelectorAll("[data-annul-payment]").forEach(b=>b.addEventListener("click",()=>{if(!annulForm)return;annulForm.action=b.dataset.action;annulForm.reset();openDialog(annul);}));
 const review=by("review-client"), reviewForm=review?.querySelector("[data-review-form]");
 root.querySelectorAll("[data-review-client]").forEach(b=>b.addEventListener("click",()=>{if(!reviewForm)return;reviewForm.action=b.dataset.action;reviewForm.reset();review.querySelector("[data-review-copy]").textContent=b.dataset.title||"Pago del cliente";openDialog(review);}));
 root.querySelectorAll("dialog").forEach(d=>d.addEventListener("click",e=>{if(e.target!==d)return;const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close?.();}));
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
document.addEventListener("dirtec:workspace:loaded",init);
})();
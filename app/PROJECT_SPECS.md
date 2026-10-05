# Kora — Alpha Project Specification

## Alpha Goal

The goal of the Kora Alpha is to deliver a reliable WhatsApp-based business assistant that allows a small business owner to **manage inventory, record transactions, and understand business performance through natural conversation**.

For Alpha, development will focus on three core areas:

**Inventory → Transactions → Insights**

The priority is not adding more features. It is making these three workflows reliable from end to end.

---

## 1. Inventory Management

Kora should maintain an accurate view of what the business currently has in stock.

### Features
- Add a new product
- Set initial stock quantity
- Increase stock
- Reduce stock
- Check stock for a product
- View current inventory
- Update product information
- Set cost and selling price
- Low-stock detection

### What Must Be Perfected
- Product/entity extraction from natural messages
- Multi-message conversations and slot collection
- Product name matching and aliases
- Quantity and unit handling
- Prevention of invalid stock changes
- Correct inventory updates after sales/purchases
- Clear confirmation and error messages

---

## 2. Transactions

Kora should accurately record money entering and leaving the business.

### Features

**Sales**
- Record a sale
- Automatically reduce inventory
- Record quantity, product and amount
- View recent sales

**Purchases**
- Record stock purchases
- Automatically increase inventory
- Record purchase cost

**Expenses**
- Record business expenses
- Categorise expenses
- View recent expenses

### What Must Be Perfected
- Transaction extraction
- Multi-message transaction completion
- Inventory/transaction consistency
- Validation before execution
- Duplicate transaction protection
- Correct handling of incomplete information
- Ability to correct/cancel mistakes
- Reliable transaction history

---

## 3. Business Insights

Kora should turn stored business data into simple, useful answers.

### Features
- Today's sales
- Today's expenses
- Daily profit estimate
- Weekly/monthly summaries
- Best-selling products
- Low-stock products
- Sales by product
- Expense breakdown
- Basic business performance summaries

Example:

> **Owner:** How did I do today?
>
> **Kora:** You made £420 in sales and recorded £270 in expenses today. Your estimated profit was £150. Coca-Cola was your best-selling product with 18 units sold.

### What Must Be Perfected
- Accurate calculations from transaction data
- Correct date/time filtering
- Reliable aggregation
- Natural-language insight queries
- Short, understandable responses
- Clear distinction between revenue, expenses and profit

---

## Alpha Conversation Engine

All three areas depend on a reliable conversational system.

Before Alpha, Kora must reliably support:

- Multi-message commands
- Persistent unfinished tasks through Redis
- Slot merging across messages
- Missing-information detection
- Context-aware follow-up messages
- Intent switching/cancellation
- Task completion and session clearing
- Ambiguous input handling
- Graceful fallback when Kora does not understand

The core principle is:

**Redis stores unfinished work. PostgreSQL stores business truth.**

---

## Alpha Success Criteria

A user should be able to operate their basic business records for an entire day through WhatsApp without needing to understand Kora's internal commands.

The complete loop must work reliably:

**Stock comes in → inventory updates → product is sold → transaction is recorded → inventory decreases → expenses are recorded → owner asks about the business → Kora provides an accurate summary.**

Anything outside **Inventory, Transactions, Insights, and the conversation infrastructure required to support them** is secondary until the Alpha is stable.
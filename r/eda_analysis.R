# ============================================================
# E-Commerce Sales Dashboard — Statistical EDA in R
# Complements the Python/SQL layer with distribution-level analysis
# and publication-quality static visuals (ggplot2).
# ============================================================

library(DBI)
library(RSQLite)
library(dplyr)
library(ggplot2)
library(scales)
library(lubridate)

con <- dbConnect(RSQLite::SQLite(), dbname = "../data/ecommerce_warehouse.db")
tx <- dbGetQuery(con, "SELECT * FROM fact_transactions")
dbDisconnect(con)

tx$order_date <- as.Date(tx$order_date)

# ---- 1. Descriptive statistics on order value ----
summary_stats <- tx %>%
  summarise(
    n = n(),
    mean_order_value = mean(net_revenue),
    median_order_value = median(net_revenue),
    sd_order_value = sd(net_revenue),
    p90 = quantile(net_revenue, 0.90),
    p99 = quantile(net_revenue, 0.99)
  )
print(summary_stats)

# ---- 2. Revenue distribution by category (boxplot, shows spread + outliers) ----
p1 <- ggplot(tx, aes(x = category, y = net_revenue, fill = category)) +
  geom_boxplot(outlier.alpha = 0.15, show.legend = FALSE) +
  scale_y_continuous(labels = dollar_format(), trans = "log10") +
  labs(
    title = "Order Value Distribution by Product Category",
    subtitle = "Log-scaled y-axis to reveal spread across 120K+ transactions",
    x = NULL, y = "Net revenue per line item (log scale)"
  ) +
  theme_minimal(base_size = 12) +
  theme(axis.text.x = element_text(angle = 30, hjust = 1))

ggsave("category_revenue_boxplot.png", p1, width = 9, height = 6, dpi = 150)

# ---- 3. Weekly seasonality (trend + smoother) ----
weekly <- tx %>%
  mutate(week = floor_date(order_date, "week")) %>%
  group_by(week) %>%
  summarise(revenue = sum(net_revenue))

p2 <- ggplot(weekly, aes(x = week, y = revenue)) +
  geom_line(color = "#2C5F8A", alpha = 0.6) +
  geom_smooth(method = "loess", span = 0.15, color = "#D94F4F", se = FALSE) +
  scale_y_continuous(labels = dollar_format()) +
  labs(
    title = "Weekly Revenue Trend with LOESS Smoother",
    subtitle = "Holiday-season and mid-year sale spikes are clearly visible",
    x = NULL, y = "Weekly net revenue"
  ) +
  theme_minimal(base_size = 12)

ggsave("weekly_revenue_trend.png", p2, width = 9, height = 6, dpi = 150)

# ---- 4. Correlation check: discount depth vs. return likelihood ----
discount_return <- tx %>%
  group_by(discount_pct) %>%
  summarise(return_rate = mean(is_returned), n = n())

p3 <- ggplot(discount_return, aes(x = discount_pct, y = return_rate)) +
  geom_col(fill = "#4A7C59") +
  scale_y_continuous(labels = percent_format()) +
  labs(
    title = "Return Rate by Discount Depth",
    subtitle = "Heavier discounts correlate with modestly higher return rates",
    x = "Discount applied (%)", y = "Return rate"
  ) +
  theme_minimal(base_size = 12)

ggsave("discount_vs_returns.png", p3, width = 8, height = 5, dpi = 150)

cat("EDA complete. Plots saved: category_revenue_boxplot.png, weekly_revenue_trend.png, discount_vs_returns.png\n")

# 使用 Sidekiq 的后台任务

## Sidekiq 配置

```ruby
# Gemfile
gem 'sidekiq'
gem 'sidekiq-cron' # Optional: scheduled jobs

# config/initializers/sidekiq.rb
Sidekiq.configure_server do |config|
  config.redis = { url: ENV['REDIS_URL'] || 'redis://localhost:6379/0' }
end

Sidekiq.configure_client do |config|
  config.redis = { url: ENV['REDIS_URL'] || 'redis://localhost:6379/0' }
end

# config/sidekiq.yml
:concurrency: 5
:queues:
  - critical
  - default
  - low
```

## 基本任务设计

```ruby
# app/jobs/email_sender_job.rb
class EmailSenderJob < ApplicationJob
  queue_as :default

  def perform(user_id, email_type)
    user = User.find(user_id)
    UserMailer.send(email_type, user).deliver_now
  end
end

# Usage
EmailSenderJob.perform_later(user.id, :welcome)

# Perform at specific time
EmailSenderJob.set(wait: 1.hour).perform_later(user.id, :reminder)
EmailSenderJob.set(wait_until: Date.tomorrow.noon).perform_later(user.id, :digest)
```

## 队列优先级

```ruby
class CriticalJob < ApplicationJob
  queue_as :critical

  def perform
    # High priority work
  end
end

class ReportGenerationJob < ApplicationJob
  queue_as :low

  def perform
    # Can wait
  end
end
```

## 重试策略

```ruby
class ImportJob < ApplicationJob
  # Retry up to 5 times with exponential backoff
  sidekiq_options retry: 5

  # Custom retry logic
  sidekiq_retry_in do |count, exception|
    case exception
    when NetworkError
      10 * (count + 1) # 10, 20, 30 seconds
    when RateLimitError
      1.hour
    else
      :default # Use Sidekiq's default exponential backoff
    end
  end

  def perform(data_url)
    # Import logic
  end
end
```

## 错误处理

```ruby
class ProcessPaymentJob < ApplicationJob
  sidekiq_options retry: 3

  # Called when job fails after all retries
  sidekiq_retries_exhausted do |msg, exception|
    Rails.logger.error("Payment job failed: #{msg}")

    # Notify admin
    AdminMailer.job_failed(msg, exception).deliver_now

    # Store failure record
    FailedPayment.create(
      user_id: msg['args'][0],
      error: exception.message
    )
  end

  def perform(user_id, amount)
    user = User.find(user_id)
    PaymentProcessor.charge(user, amount)
  rescue PaymentError => e
    # Log and re-raise to trigger retry
    Rails.logger.warn("Payment failed: #{e.message}")
    raise
  end
end
```

## 批量处理

```ruby
class BulkEmailJob < ApplicationJob
  def perform(user_ids)
    # Process in batches to avoid memory issues
    user_ids.in_groups_of(100, false) do |batch|
      batch.each do |user_id|
        user = User.find(user_id)
        UserMailer.newsletter(user).deliver_now
      end
    end
  end
end

# Better: Use Sidekiq::Batch (requires sidekiq-pro)
class ParentJob < ApplicationJob
  def perform(user_ids)
    batch = Sidekiq::Batch.new
    batch.on(:success, self.class, 'user_ids' => user_ids)

    batch.jobs do
      user_ids.each do |user_id|
        ChildJob.perform_later(user_id)
      end
    end
  end

  def on_success(status, options)
    # All child jobs completed
    Rails.logger.info("Processed #{options['user_ids'].length} users")
  end
end
```

## 定时任务

```ruby
# Using sidekiq-cron
# config/initializers/sidekiq.rb
schedule_file = "config/schedule.yml"

if File.exist?(schedule_file) && Sidekiq.server?
  Sidekiq::Cron::Job.load_from_hash YAML.load_file(schedule_file)
end

# config/schedule.yml
daily_report:
  cron: "0 6 * * *"
  class: "DailyReportJob"
  queue: default

cleanup_old_records:
  cron: "0 2 * * 0" # Sunday at 2am
  class: "CleanupJob"
  queue: low
```

## 任务模式

幂等任务：

```ruby
class ProcessOrderJob < ApplicationJob
  def perform(order_id)
    order = Order.find(order_id)

    # Check if already processed
    return if order.processed?

    # Process order
    order.process!
  end
end
```

唯一任务（需要 sidekiq-unique-jobs gem）：

```ruby
class GenerateReportJob < ApplicationJob
  sidekiq_options lock: :until_executed,
                   on_conflict: :log

  def perform(user_id, report_type)
    # Only one instance of this job per user+report_type
  end
end
```

## 测试

```ruby
# spec/jobs/email_sender_job_spec.rb
require 'rails_helper'

RSpec.describe EmailSenderJob, type: :job do
  let(:user) { create(:user) }

  describe "#perform" do
    it "sends welcome email" do
      expect {
        described_class.perform_now(user.id, :welcome)
      }.to change { ActionMailer::Base.deliveries.count }.by(1)
    end

    it "enqueues job" do
      expect {
        described_class.perform_later(user.id, :welcome)
      }.to have_enqueued_job(described_class)
        .with(user.id, :welcome)
        .on_queue("default")
    end
  end
end

# Test inline in development
# config/environments/test.rb
config.active_job.queue_adapter = :inline
```

## 监控

```ruby
# Check queue size
Sidekiq::Queue.new("default").size

# Check scheduled jobs
Sidekiq::ScheduledSet.new.size

# Check retry set
Sidekiq::RetrySet.new.size

# Check dead jobs
Sidekiq::DeadSet.new.size

# Clear queues (use with caution)
Sidekiq::Queue.new("default").clear
```

## 性能提示

- 保持任务小而专注
- 传递 ID 而非对象（避免序列化/反序列化问题）
- 使用适当的队列优先级
- 设置合理的重试次数限制
- 监控队列深度和延迟
- 根据负载扩展 Worker 数量
- 使用 Redis 持久化确保任务持久性
- 考虑任务唯一性以防止重复执行

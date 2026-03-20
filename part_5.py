java_skill = {
  "skill_id": "java",
  "skill_name": "Java",
  "category": "backend_development",
  "total_questions": 1,
  "levels": {
    "intermediate": [
      {"question_id":"java_int_001","type":"mcq","question":"In Java, which collection class is thread-safe and allows concurrent read access without locking the entire object?","options":["HashMap","Hashtable","ConcurrentHashMap","Collections.synchronizedMap()"],"correct_answer":2,"explanation":"ConcurrentHashMap divides the map into segments (or uses CAS operations in Java 8+) allowing multiple threads to read and write concurrently without a global lock.","difficulty_score":6,"time_seconds":60,"tags":["concurrency","collections","Java"],"prerequisites":[],"common_mistakes":["Assuming Collections.synchronizedMap is the most performant"],"learning_resources":["https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ConcurrentHashMap.html"],"real_world_context":"High-throughput Java backend services rely on ConcurrentHashMap for shared caching."}
    ]
  }
}

go_skill = {
  "skill_id": "golang",
  "skill_name": "Go (Golang)",
  "category": "backend_development",
  "total_questions": 1,
  "levels": {
    "beginner": [
      {"question_id":"go_beg_001","type":"mcq","question":"How do you start a new concurrent execution unit in Go?","options":["new Thread(func)","go func()","spawn func()","async func()"],"correct_answer":1,"explanation":"The `go` keyword followed by a function call launches a new goroutine, a lightweight thread managed by the Go runtime.","difficulty_score":3,"time_seconds":30,"tags":["goroutines","concurrency","Go"],"prerequisites":[],"common_mistakes":["Thinking Go uses OS threads directly 1:1"],"learning_resources":["https://go.dev/tour/concurrency/1"],"real_world_context":"Goroutines allow Go servers to easily handle thousands of concurrent requests."}
    ]
  }
}

rust_skill = {
  "skill_id": "rust",
  "skill_name": "Rust",
  "category": "systems_programming",
  "total_questions": 1,
  "levels": {
    "intermediate": [
      {"question_id":"rust_int_001","type":"mcq","question":"What Rust feature ensures memory safety at compile time by tracking the lifetime and ownership of references?","options":["Garbage Collector","The Borrow Checker","Smart Pointers","Reference Counting"],"correct_answer":1,"explanation":"The Borrow Checker is a component of the Rust compiler that statically verifies all references are valid, ensuring no dangling pointers or data races exist without needing a garbage collector.","difficulty_score":7,"time_seconds":60,"tags":["borrow_checker","ownership","memory_safety"],"prerequisites":[],"common_mistakes":["Believing Rust has a JVM-like Garbage Collector"],"learning_resources":["https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html"],"real_world_context":"The borrow checker is why Rust is replacing C/C++ in performance-critical system components."}
    ]
  }
}

skills = [java_skill, go_skill, rust_skill]

#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/list.h>
#include <linux/slab.h>

struct birthday {
	int day;
	int month;
	int year;
	struct list_head list;	
};

struct list_head birthday_list;

struct birthday *createBirthday(int day, int month, int year) {
	struct birthday *person = kmalloc(sizeof(struct birthday), GFP_KERNEL);
	person->day = day;
	person->month = month;
	person->year = year;
	return person;
}

void printInfo(char *str) {
	printk(KERN_INFO "OS Module: %s", str);
}

int simple_init(void)
{
	printInfo("Loading Module\n");
	
	LIST_HEAD(birthday_list);

        struct birthday *person = createBirthday(9, 11, 2000);
	list_add_tail(&person->list, &birthday_list);
	person = createBirthday(19, 06, 1997);
	list_add_tail(&person->list, &birthday_list);
	person = createBirthday(24, 8, 1974);
	list_add_tail(&person->list, &birthday_list);
	person = createBirthday(30, 3, 1965);
	list_add_tail(&person->list, &birthday_list);
	person = createBirthday(9, 1, 1996);
	list_add_tail(&person->list, &birthday_list);

	struct birthday *ptr;

	list_for_each_entry(ptr, &birthday_list, list) {
		printk(KERN_INFO "OS Module: Day %d.%d.%d\n", ptr->day, ptr->month, ptr->year);
	}

       return 0;
}

void simple_exit(void) {
	printInfo("Removing Module\n");

	struct birthday *tmp;
	struct list_head *ptr, *next;

	if (list_empty(&birthday_list)) {
		printInfo("List is empty");
		return;
	}

	list_for_each_safe(ptr, next, &birthday_list){
		tmp = list_entry(ptr, struct birthday, list);
		printk(KERN_INFO "OS Module: Removing %d.%d.%d\n", tmp->day, tmp->month, tmp->year);
		list_del(ptr);
		kfree(tmp);
	}

	printInfo("Module removed\n");
}

module_init( simple_init );
module_exit( simple_exit );

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Non Simple Module");
MODULE_AUTHOR("AA");
